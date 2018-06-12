from grr_api_client import api

grr_api = api.InitHttp(api_endpoint='http://localhost:8000', auth=('admin', 'e2e_tests'))

print("Username of admin user is %s" % grr_api.username)
