import os
import requests
import urlparse

api_url = os.environ.get("APPVEYOR_API_URL")
print("Using Appveyor API url %s" % api_url)

if api_url:
  tests_endpoint = urlparse.urljoin(api_url, "api/tests")
  resp = requests.post(tests_endpoint, data={
    "testName": "Dummy Test",
    "testFramework": "JUnit",
    "fileName": os.path.relpath(__file__),
    "outcome": "Passed",
    "durationMilliseconds": "1200",
    "ErrorMessage": "",
    "ErrorStackTrace": "",
    "StdOut": "",
    "StdErr": ""
  })
  print("Received response: %s" % resp)
