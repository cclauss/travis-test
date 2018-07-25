import glob

from grr_response_core.lib import utils


class UtmpStruct(utils.Struct):
  """Parse wtmp file from utmp.h."""
  _fields = [
    ("h", "ut_type"),
    ("i", "ut_pid"),
    ("32s", "ut_line"),
    ("4s", "ut_id"),
    ("32s", "ut_user"),
    ("256s", "ut_host"),
    ("i", "ut_exit"),
    ("i", "ut_session"),
    ("i", "tv_sec"),
    ("i", "tv_usec"),
    ("4i", "ut_addr_v6"),
    ("20s", "unused"),
  ]


class EnumerateUsers(object):
  @classmethod
  def ParseWtmp(cls):
    users = {}

    wtmp_struct_size = UtmpStruct.GetSize()
    filenames = glob.glob("/var/log/wtmp*") + ["/var/run/utmp"]

    for filename in filenames:
      try:
        wtmp = open(filename, "rb").read()
      except IOError:
        continue

      for offset in xrange(0, len(wtmp), wtmp_struct_size):
        try:
          record = UtmpStruct(wtmp[offset:offset + wtmp_struct_size])
        except utils.ParsingError:
          break

        # Users only appear for USER_PROCESS events, others are system.
        if record.ut_type != 7:
          continue

        try:
          if users[record.ut_user] < record.tv_sec:
            users[record.ut_user] = record.tv_sec
        except KeyError:
          users[record.ut_user] = record.tv_sec

    return users

  def Run(self):
    """Enumerates all the users on this system."""
    parse_result = self.ParseWtmp()
    users = []
    for user, last_login in parse_result.iteritems():
      # Lose the null termination
      username = user.split("\x00", 1)[0]

      if username:
        # Somehow the last login time can be < 0. There is no documentation
        # what this means so we just set it to 0 (the rdfvalue field is
        # unsigned so we can't send negative values).
        if last_login < 0:
          last_login = 0
      users.append((username, last_login))
    print(users)


if __name__ == "__main__":
  EnumerateUsers().Run()
