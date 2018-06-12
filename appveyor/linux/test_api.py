import requests
import time

from grr_api_client import api

grr_api = api.InitHttp(api_endpoint='http://localhost:8000', auth=('admin', 'e2e_tests'))

MAX_RETRIES = 30

tries_left = MAX_RETRIES

while tries_left > 0:
  try:
    print("Username of admin user is %s" % grr_api.username)
    break
  except requests.ConnectionError as e:
    print(
      "Encountered error trying to connect to GRR API (%d tries left): %s" % (
      tries_left, e.message))
    tries_left -= 1
    if tries_left <= 0:
      raise e
  time.sleep(1)
