"""Trivial script used for waiting until the GRR API has initialized."""

import os
import requests
import time

from grr_api_client import api


MAX_RETRIES = 30


if __name__ == "__main__":
  # TODO(ogaro): Use pre-assigned port.
  grr_api = api.InitHttp(
      api_endpoint='http://localhost:8000',
      auth=('admin', os.environ["GRR_ADMIN_PASS"]))

  tries_left = MAX_RETRIES

  while tries_left > 0:
    try:
      # Try loading all clients in the datastore.
      _ = list(grr_api.SearchClients())
      break
    except requests.ConnectionError as e:
      # TODO(ogaro): Try logging library.
      print(
        "Encountered error trying to connect to GRR API (%d tries left): %s" % (
        tries_left, e.message))
      tries_left -= 1
      if tries_left <= 0:
        raise e
    time.sleep(1)
