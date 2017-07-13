#!/usr/bin/env python
"""A collection of records stored sequentially.
"""

import collections
import random
import threading
import time

from grr.lib import access_control
from grr.lib import data_store
from grr.lib import rdfvalue
from grr.lib import registry
from grr.lib import utils

from grr.lib.rdfvalues import flows as rdf_flows
from grr.lib.rdfvalues import protodict as rdf_protodict


class SequentialCollection(object):
  """A sequential collection of RDFValues.

  This class supports the writing of individual RDFValues and the sequential
  reading of them.

  """

  # The type which we store, subclasses must set this to a subclass of RDFValue.
  RDF_TYPE = None

  # The attribute (column) where we store value.
  ATTRIBUTE = "aff4:sequential_value"

  # The largest possible suffix - maximum value expressible by 6 hex digits.
  MAX_SUFFIX = 2**24 - 1

  def __init__(self, collection_id, token=None):
    super(SequentialCollection, self).__init__()
    # The collection_id for this collection is a RDFURN for now.
    self.collection_id = collection_id
    self.token = token

  @classmethod
  def _MakeURN(cls, urn, timestamp, suffix=None):
    if suffix is None:
      # Disallow 0 so that subtracting 1 from a normal suffix doesn't require
      # special handling.
      suffix = random.randint(1, cls.MAX_SUFFIX)
    return urn.Add("Results").Add("%016x.%06x" % (timestamp, suffix))

  @classmethod
  def _ParseURN(cls, urn):
    string_urn = utils.SmartUnicode(urn)
    if len(string_urn) < 31 or string_urn[-7] != ".":
      return None
    return (int(string_urn[-23:-7], 16), int(string_urn[-6:], 16))

  @classmethod
  def StaticAdd(cls,
                collection_urn,
                token,
                rdf_value,
                timestamp=None,
                suffix=None,
                mutation_pool=None,
                **kwargs):
    """Adds an rdf value to a collection.

    Adds an rdf value to a collection. Does not require that the collection be
    open. NOTE: The caller is responsible for ensuring that the collection
    exists and is of the correct type.

    Args:
      collection_urn: The urn of the collection to add to.

      token: The database access token to write with.

      rdf_value: The rdf value to add to the collection.

      timestamp: The timestamp (in microseconds) to store the rdf value
          at. Defaults to the current time.

      suffix: A 'fractional timestamp' suffix to reduce the chance of
          collisions. Defaults to a random number.

      mutation_pool: An optional MutationPool object to write to. If not given,
                     the data_store is used directly.

      **kwargs: Keyword arguments to pass through to the underlying database
        call.

    Returns:
      The pair (timestamp, suffix) which identifies the value within the
      collection.

    Raises:
      ValueError: rdf_value has unexpected type.

    """
    if not isinstance(rdf_value, cls.RDF_TYPE):
      raise ValueError("This collection only accepts values of type %s." %
                       cls.RDF_TYPE.__name__)

    if timestamp is None:
      timestamp = rdfvalue.RDFDatetime.Now()
    if isinstance(timestamp, rdfvalue.RDFDatetime):
      timestamp = timestamp.AsMicroSecondsFromEpoch()

    if not rdf_value.age:
      rdf_value.age = rdfvalue.RDFDatetime.Now()

    if not isinstance(collection_urn, rdfvalue.RDFURN):
      collection_urn = rdfvalue.RDFURN(collection_urn)

    result_subject = cls._MakeURN(collection_urn, timestamp, suffix)
    if mutation_pool:
      mutation_pool.Set(
          result_subject,
          cls.ATTRIBUTE,
          rdf_value.SerializeToString(),
          timestamp=timestamp,
          **kwargs)
    else:
      data_store.DB.Set(
          result_subject,
          cls.ATTRIBUTE,
          rdf_value.SerializeToString(),
          timestamp=timestamp,
          token=token,
          **kwargs)

    return cls._ParseURN(result_subject)

  def Add(self, rdf_value, timestamp=None, suffix=None, **kwargs):
    """Adds an rdf value to the collection.

    Adds an rdf value to the collection. Does not require that the collection
    be locked.

    Args:
      rdf_value: The rdf value to add to the collection.

      timestamp: The timestamp (in microseconds) to store the rdf value
          at. Defaults to the current time.

      suffix: A 'fractional timestamp' suffix to reduce the chance of
          collisions. Defaults to a random number.

      **kwargs: Keyword arguments to pass through to the underlying database
        call.

    Returns:
      The pair (timestamp, suffix) which identifies the value within the
      collection.

    Raises:
      ValueError: rdf_value has unexpected type.

    """
    return self.StaticAdd(
        self.collection_id,
        self.token,
        rdf_value,
        timestamp=timestamp,
        suffix=suffix,
        **kwargs)

  def Scan(self, after_timestamp=None, include_suffix=False, max_records=None):
    """Scans for stored records.

    Scans through the collection, returning stored values ordered by timestamp.

    Args:

      after_timestamp: If set, only returns values recorded after timestamp.

      include_suffix: If true, the timestamps returned are pairs of the form
        (micros_since_epoc, suffix) where suffix is a 24 bit random refinement
        to avoid collisions. Otherwise only micros_since_epoc is returned.

      max_records: The maximum number of records to return. Defaults to
        unlimited.

    Yields:
      Pairs (timestamp, rdf_value), indicating that rdf_value was stored at
      timestamp.

    """
    after_urn = None
    if after_timestamp is not None:
      if isinstance(after_timestamp, tuple):
        suffix = after_timestamp[1]
        after_timestamp = after_timestamp[0]
      else:
        suffix = self.MAX_SUFFIX
      after_urn = utils.SmartStr(
          self._MakeURN(self.collection_id, after_timestamp, suffix=suffix))

    for subject, timestamp, value in data_store.DB.ScanAttribute(
        self.collection_id.Add("Results"),
        self.ATTRIBUTE,
        after_urn=after_urn,
        max_records=max_records,
        token=self.token):
      rdf_value = self.RDF_TYPE.FromSerializedString(value)
      rdf_value.age = timestamp
      if include_suffix:
        yield (self._ParseURN(subject), rdf_value)
      else:
        yield (timestamp, rdf_value)

  def MultiResolve(self, timestamps):
    """Lookup multiple values by (timestamp, suffix) pairs."""
    for _, v in data_store.DB.MultiResolvePrefix(
        [
            self._MakeURN(self.collection_id, ts, suffix)
            for (ts, suffix) in timestamps
        ],
        self.ATTRIBUTE,
        token=self.token):
      _, value, timestamp = v[0]
      rdf_value = self.RDF_TYPE.FromSerializedString(value)
      rdf_value.age = timestamp
      yield rdf_value

  def __iter__(self):
    for _, item in self.Scan():
      yield item

  def Delete(self):
    pool = data_store.DB.GetMutationPool(self.token)
    with pool:
      for subject, _, _ in data_store.DB.ScanAttribute(
          self.collection_id.Add("Results"), self.ATTRIBUTE, token=self.token):
        pool.DeleteSubject(subject)
        if pool.Size() > 50000:
          pool.Flush()


class BackgroundIndexUpdater(object):
  """Updates IndexedSequentialCollection objects in the background."""
  INDEX_DELAY = 240

  exit_now = False

  def __init__(self):
    self.to_process = collections.deque()
    self.cv = threading.Condition()

  def ExitNow(self):
    with self.cv:
      self.exit_now = True
      self.to_process.append(None)
      self.cv.notify()

  def AddIndexToUpdate(self, collection_cls, index_urn):
    with self.cv:
      self.to_process.append((collection_cls, index_urn,
                              time.time() + self.INDEX_DELAY))
      self.cv.notify()

  def ProcessCollection(self, collection_cls, collection_id, token):
    collection_cls(collection_id, token=token).UpdateIndex()

  def UpdateLoop(self):
    token = access_control.ACLToken(
        username="Background Index Updater", reason="Updating An Index")
    while not self.exit_now:
      with self.cv:
        while not self.to_process:
          self.cv.wait()
        next_update = self.to_process.popleft()
        if next_update is None:
          return

      now = time.time()
      next_cls = next_update[0]
      next_urn = next_update[1]
      next_time = next_update[2]
      while now < next_time:
        time.sleep(next_time - now)
        now = time.time()

      self.ProcessCollection(next_cls, next_urn, token)


BACKGROUND_INDEX_UPDATER = BackgroundIndexUpdater()


class UpdaterStartHook(registry.InitHook):

  def RunOnce(self):
    t = threading.Thread(
        None,
        BACKGROUND_INDEX_UPDATER.UpdateLoop,
        name="SequentialCollectionIndexUpdater")
    t.daemon = True
    t.start()


class IndexedSequentialCollection(SequentialCollection):
  """An indexed sequential collection of RDFValues.

  Adds an index to SequentialCollection, making it efficient to find the number
  of records present, and to find a particular record number.

  IMPLEMENTATION NOTE: The index is created lazily, and for records older than
    INDEX_WRITE_DELAY.
  """

  # How many records between index entries. Subclasses may change this.  The
  # full index must fit comfortably in RAM, default is meant to be reasonable
  # for collections of up to ~1b small records. (Assumes we can have ~1m index
  # points in ram, and that reading 1k records is reasonably fast.)

  INDEX_SPACING = 1024

  # An attribute name of the form "index:sc_<i>" at timestamp <t> indicates that
  # the item with record number i was stored at timestamp t. The timestamp
  # suffix is stored as the value.

  INDEX_ATTRIBUTE_PREFIX = "index:sc_"

  # The time to wait before creating an index for a record - hacky defense
  # against the correct index changing due to a late write.

  INDEX_WRITE_DELAY = rdfvalue.Duration("3m")

  def __init__(self, *args, **kwargs):
    super(IndexedSequentialCollection, self).__init__(*args, **kwargs)
    self._index = None

  def _ReadIndex(self):
    if self._index:
      return
    self._index = {0: (0, 0)}
    self._max_indexed = 0
    for (attr, value, ts) in data_store.DB.ResolvePrefix(
        self.collection_id, self.INDEX_ATTRIBUTE_PREFIX, token=self.token):
      i = int(attr[len(self.INDEX_ATTRIBUTE_PREFIX):], 16)
      self._index[i] = (ts, int(value, 16))
      self._max_indexed = max(i, self._max_indexed)

  def _MaybeWriteIndex(self, i, ts, mutation_pool):
    """Write index marker i."""
    if i > self._max_indexed and i % self.INDEX_SPACING == 0:
      # We only write the index if the timestamp is more than 5 minutes in the
      # past: hacky defense against a late write changing the count.
      if ts[0] < (rdfvalue.RDFDatetime.Now() -
                  self.INDEX_WRITE_DELAY).AsMicroSecondsFromEpoch():
        # We may be used in contexts were we don't have write access, so simply
        # give up in that case. TODO(user): Remove this when the ACL
        # system allows.
        try:
          mutation_pool.Set(
              self.collection_id,
              self.INDEX_ATTRIBUTE_PREFIX + "%08x" % i,
              "%06x" % ts[1],
              timestamp=ts[0],
              replace=True)
          self._index[i] = ts
          self._max_indexed = max(i, self._max_indexed)
        except access_control.UnauthorizedAccess:
          pass

  def _IndexedScan(self, i, max_records=None):
    """Scan records starting with index i."""
    self._ReadIndex()

    # The record number that we will read next.
    idx = 0
    # The timestamp that we will start reading from.
    start_ts = 0
    if i >= self._max_indexed:
      start_ts = max((0, 0), (self._index[self._max_indexed][0],
                              self._index[self._max_indexed][1] - 1))
      idx = self._max_indexed
    else:
      try:
        possible_idx = i - i % self.INDEX_SPACING
        start_ts = (max(0, self._index[possible_idx][0]),
                    self._index[possible_idx][1] - 1)
        idx = possible_idx
      except KeyError:
        pass

    if max_records is not None:
      max_records += i - idx

    with data_store.DB.GetMutationPool(token=self.token) as mutation_pool:
      for (ts, value) in self.Scan(
          after_timestamp=start_ts,
          max_records=max_records,
          include_suffix=True):
        self._MaybeWriteIndex(idx, ts, mutation_pool)
        if idx >= i:
          yield (idx, ts, value)
        idx += 1

  def GenerateItems(self, offset=0):
    for (_, _, value) in self._IndexedScan(offset):
      yield value

  def __getitem__(self, index):
    if index >= 0:
      for (_, _, value) in self._IndexedScan(index, max_records=1):
        return value
      raise IndexError("collection index out of range")
    else:
      raise RuntimeError("Index must be >= 0")

  def CalculateLength(self):
    self._ReadIndex()
    highest_index = None
    for (i, _, _) in self._IndexedScan(self._max_indexed):
      highest_index = i
    if highest_index is None:
      return 0
    return highest_index + 1

  def __len__(self):
    return self.CalculateLength()

  def UpdateIndex(self):
    self._ReadIndex()
    for _ in self._IndexedScan(self._max_indexed):
      pass

  @classmethod
  def StaticAdd(cls,
                collection_urn,
                token,
                rdf_value,
                timestamp=None,
                suffix=None,
                **kwargs):
    r = super(IndexedSequentialCollection, cls).StaticAdd(
        collection_urn, token, rdf_value, timestamp, suffix, **kwargs)
    if random.randint(0, cls.INDEX_SPACING) == 0:
      BACKGROUND_INDEX_UPDATER.AddIndexToUpdate(cls, collection_urn)
    return r


class GeneralIndexedCollection(IndexedSequentialCollection):
  """An indexed sequential collection of RDFValues with different types."""
  RDF_TYPE = rdf_protodict.EmbeddedRDFValue

  @classmethod
  def StaticAdd(cls, collection_urn, token, rdf_value, **kwargs):
    if not rdf_value.age:
      rdf_value.age = rdfvalue.RDFDatetime.Now()

    super(GeneralIndexedCollection, cls).StaticAdd(
        collection_urn,
        token,
        rdf_protodict.EmbeddedRDFValue(payload=rdf_value),
        **kwargs)

  def Scan(self, **kwargs):
    for (timestamp, rdf_value) in super(GeneralIndexedCollection, self).Scan(
        **kwargs):
      yield (timestamp, rdf_value.payload)


class GrrMessageCollection(IndexedSequentialCollection):
  """Sequential HuntResultCollection."""
  RDF_TYPE = rdf_flows.GrrMessage

  def AddAsMessage(self, rdfvalue_in, source):
    """Helper method to add rdfvalues as GrrMessages for testing."""
    self.Add(rdf_flows.GrrMessage(payload=rdfvalue_in, source=source))
