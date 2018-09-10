#!/usr/bin/env python
"""Utililies for modifying the GRR server configuration."""
from __future__ import print_function

import getpass
import os
import re
# importing readline enables the raw_input calls to have history etc.
import readline  # pylint: disable=unused-import
import socket
import subprocess
import sys
import time


import builtins
from future.moves.urllib import parse as urlparse
from future.utils import iteritems
import MySQLdb
from MySQLdb.constants import CR as mysql_conn_errors
from MySQLdb.constants import ER as general_mysql_errors
import pkg_resources

# pylint: disable=unused-import,g-bad-import-order
from grr_response_server import server_plugins
# pylint: enable=g-bad-import-order,unused-import

from grr_response_core import config as grr_config

from grr_response_core.lib import flags
from grr_response_core.lib import rdfvalue
from grr_response_core.lib import repacking
from grr_response_core.lib import utils
from grr_response_core.lib.rdfvalues import crypto as rdf_crypto
from grr_response_server import access_control
from grr_response_server import aff4
from grr_response_server import key_utils
from grr_response_server import maintenance_utils
from grr_response_server import server_startup

# These control retry behavior when checking that GRR can connect to
# MySQL during config initialization.
_MYSQL_MAX_RETRIES = 2
_MYSQL_RETRY_WAIT_SECS = 2


class ConfigInitError(Exception):
  """Exception raised to abort config initialization."""

  def __init__(self):
    super(ConfigInitError, self).__init__(
        "Aborting config initialization. Please run 'grr_config_updater "
        "initialize' to retry initialization.")


def ImportConfig(filename, config):
  """Reads an old config file and imports keys and user accounts."""
  sections_to_import = ["PrivateKeys"]
  entries_to_import = [
      "Client.executable_signing_public_key", "CA.certificate",
      "Frontend.certificate"
  ]
  options_imported = 0
  old_config = grr_config.CONFIG.MakeNewConfig()
  old_config.Initialize(filename)

  for entry in old_config.raw_data:
    try:
      section = entry.split(".")[0]
      if section in sections_to_import or entry in entries_to_import:
        config.Set(entry, old_config.Get(entry))
        print("Imported %s." % entry)
        options_imported += 1

    except Exception as e:  # pylint: disable=broad-except
      print("Exception during import of %s: %s" % (entry, e))
  return options_imported


def GenerateCSRFKey(config):
  """Update a config with a random csrf key."""
  secret_key = config.Get("AdminUI.csrf_secret_key", None)
  if not secret_key:
    # TODO(amoser): Remove support for django_secret_key.
    secret_key = config.Get("AdminUI.django_secret_key", None)
    if secret_key:
      config.Set("AdminUI.csrf_secret_key", secret_key)

  if not secret_key:
    key = utils.GeneratePassphrase(length=100)
    config.Set("AdminUI.csrf_secret_key", key)
  else:
    print("Not updating csrf key as it is already set.")


def GenerateKeys(config, overwrite_keys=False):
  """Generate the keys we need for a GRR server."""
  if not hasattr(key_utils, "MakeCACert"):
    flags.PARSER.error("Generate keys can only run with open source key_utils.")
  if (config.Get("PrivateKeys.server_key", default=None) and
      not overwrite_keys):
    print(config.Get("PrivateKeys.server_key"))
    raise RuntimeError("Config %s already has keys, use --overwrite_keys to "
                       "override." % config.parser)

  length = grr_config.CONFIG["Server.rsa_key_length"]
  print("All keys will have a bit length of %d." % length)
  print("Generating executable signing key")
  executable_key = rdf_crypto.RSAPrivateKey.GenerateKey(bits=length)
  config.Set("PrivateKeys.executable_signing_private_key",
             executable_key.AsPEM())
  config.Set("Client.executable_signing_public_key",
             executable_key.GetPublicKey().AsPEM())

  print("Generating CA keys")
  ca_key = rdf_crypto.RSAPrivateKey.GenerateKey(bits=length)
  ca_cert = key_utils.MakeCACert(ca_key)
  config.Set("CA.certificate", ca_cert.AsPEM())
  config.Set("PrivateKeys.ca_key", ca_key.AsPEM())

  print("Generating Server keys")
  server_key = rdf_crypto.RSAPrivateKey.GenerateKey(bits=length)
  server_cert = key_utils.MakeCASignedCert(u"grr", server_key, ca_cert, ca_key)
  config.Set("Frontend.certificate", server_cert.AsPEM())
  config.Set("PrivateKeys.server_key", server_key.AsPEM())

  print("Generating secret key for csrf protection.")
  GenerateCSRFKey(config)


def RetryQuestion(question_text, output_re="", default_val=None):
  """Continually ask a question until the output_re is matched."""
  while True:
    if default_val is not None:
      new_text = "%s [%s]: " % (question_text, default_val)
    else:
      new_text = "%s: " % question_text
    # pytype: disable=wrong-arg-count
    output = builtins.input(new_text) or str(default_val)
    # pytype: enable=wrong-arg-count
    output = output.strip()
    if not output_re or re.match(output_re, output):
      break
    else:
      print("Invalid input, must match %s" % output_re)
  return output


def RetryBoolQuestion(question_text, default_bool):
  if not isinstance(default_bool, bool):
    raise ValueError(
        "default_bool should be a boolean, not %s" % type(default_bool))
  default_val = "Y" if default_bool else "N"
  prompt_suff = "[Yn]" if default_bool else "[yN]"
  return RetryQuestion("%s %s: " % (question_text, prompt_suff), "[yY]|[nN]",
                       default_val)[0].upper() == "Y"


def ConfigureHostnames(config):
  """This configures the hostnames stored in the config."""
  if flags.FLAGS.external_hostname:
    hostname = flags.FLAGS.external_hostname
  else:
    try:
      hostname = socket.gethostname()
    except (OSError, IOError):
      print("Sorry, we couldn't guess your hostname.\n")

    hostname = RetryQuestion(
        "Please enter your hostname e.g. "
        "grr.example.com", "^[\\.A-Za-z0-9-]+$", hostname)

  print("""\n\n-=Server URL=-
The Server URL specifies the URL that the clients will connect to
communicate with the server. For best results this should be publicly
accessible. By default this will be port 8080 with the URL ending in /control.
""")
  frontend_url = RetryQuestion("Frontend URL", "^http://.*/$",
                               "http://%s:8080/" % hostname)
  config.Set("Client.server_urls", [frontend_url])

  frontend_port = urlparse.urlparse(frontend_url).port or grr_config.CONFIG.Get(
      "Frontend.bind_port")
  config.Set("Frontend.bind_port", frontend_port)

  print("""\n\n-=AdminUI URL=-:
The UI URL specifies where the Administrative Web Interface can be found.
""")
  ui_url = RetryQuestion("AdminUI URL", "^http[s]*://.*$",
                         "http://%s:8000" % hostname)
  config.Set("AdminUI.url", ui_url)
  ui_port = urlparse.urlparse(ui_url).port or grr_config.CONFIG.Get(
      "AdminUI.port")
  config.Set("AdminUI.port", ui_port)


def CheckMySQLConnection(db_options):
  """Checks whether a connection can be established to MySQL.

  Args:
    db_options: A dict mapping GRR MySQL config options to their values.

  Returns:
    A boolean indicating whether a connection could be made to a MySQL server
    instance with the given options.
  """
  for tries_left in range(_MYSQL_MAX_RETRIES, -1, -1):
    try:
      MySQLdb.connect(
          host=db_options["Mysql.host"],
          port=db_options["Mysql.port"],
          db=db_options["Mysql.database_name"],
          user=db_options["Mysql.database_username"],
          passwd=db_options["Mysql.database_password"],
          charset="utf8")
      return True
    except MySQLdb.OperationalError as mysql_op_error:
      if len(mysql_op_error.args) < 2:
        # We expect the exception's arguments to be an error-code and
        # an error message.
        print("Unexpected exception type received from MySQL. %d attempts "
              "left: %s" % (tries_left, mysql_op_error))
        time.sleep(_MYSQL_RETRY_WAIT_SECS)
        continue
      if mysql_op_error.args[0] == mysql_conn_errors.CONNECTION_ERROR:
        print("Failed to connect to MySQL. Is it running? %d attempts left." %
              tries_left)
      elif mysql_op_error.args[0] == mysql_conn_errors.UNKNOWN_HOST:
        print("Unknown-hostname error encountered while trying to connect to "
              "MySQL.")
        return False  # No need for retry.
      elif mysql_op_error.args[0] == general_mysql_errors.BAD_DB_ERROR:
        # GRR db doesn't exist yet. That's expected if this is the initial
        # setup.
        return True
      elif mysql_op_error.args[0] in (
          general_mysql_errors.ACCESS_DENIED_ERROR,
          general_mysql_errors.DBACCESS_DENIED_ERROR):
        print("Permission error encountered while trying to connect to "
              "MySQL: %s" % mysql_op_error)
        return False  # No need for retry.
      else:
        print("Unexpected operational error encountered while trying to "
              "connect to MySQL. %d attempts left: %s" % (tries_left,
                                                          mysql_op_error))
    except MySQLdb.Error as mysql_error:
      print("Unexpected error encountered while trying to connect to MySQL. "
            "%d attempts left: %s" % (tries_left, mysql_error))
    time.sleep(_MYSQL_RETRY_WAIT_SECS)
  return False


def ConfigureMySQLDatastore(config):
  """Prompts the user for configuration details for a MySQL datastore."""
  print("GRR will use MySQL as its database backend. Enter connection details:")
  datastore_init_complete = False
  db_options = {}
  while not datastore_init_complete:
    db_options["Datastore.implementation"] = "MySQLAdvancedDataStore"
    db_options["Mysql.host"] = RetryQuestion("MySQL Host", "^[\\.A-Za-z0-9-]+$",
                                             config["Mysql.host"])
    db_options["Mysql.port"] = int(
        RetryQuestion("MySQL Port (0 for local socket)", "^[0-9]+$",
                      config["Mysql.port"]))
    db_options["Mysql.database_name"] = RetryQuestion(
        "MySQL Database", "^[A-Za-z0-9-]+$", config["Mysql.database_name"])
    db_options["Mysql.database_username"] = RetryQuestion(
        "MySQL Username", "[A-Za-z0-9-@]+$", config["Mysql.database_username"])
    db_options["Mysql.database_password"] = getpass.getpass(
        prompt="Please enter password for database user %s: " %
        db_options["Mysql.database_username"])

    if CheckMySQLConnection(db_options):
      print("Successfully connected to MySQL with the provided details.")
      datastore_init_complete = True
    else:
      print("Error: Could not connect to MySQL with the provided details.")
      should_retry = RetryBoolQuestion(
          "Re-enter MySQL details? Answering 'no' will abort config "
          "initialization: ", True)
      if should_retry:
        db_options.clear()
      else:
        raise ConfigInitError()

  for option, value in iteritems(db_options):
    config.Set(option, value)


def ConfigureDatastore(config):
  """Guides the user through configuration of the datastore."""
  print("\n\n-=GRR Datastore=-\n"
        "For GRR to work each GRR server has to be able to communicate with\n"
        "the datastore. To do this we need to configure a datastore.\n")

  existing_datastore = grr_config.CONFIG.Get("Datastore.implementation")

  if not existing_datastore or existing_datastore == "FakeDataStore":
    ConfigureMySQLDatastore(config)
    return

  print("Found existing settings:\n  Datastore: %s" % existing_datastore)
  if existing_datastore == "SqliteDataStore":
    set_up_mysql = RetryBoolQuestion(
        "The SQLite datastore is no longer supported. Would you like to\n"
        "set up a MySQL datastore? Answering 'no' will abort config "
        "initialization.", True)
    if set_up_mysql:
      print("\nPlease note that no data will be migrated from SQLite to "
            "MySQL.\n")
      ConfigureMySQLDatastore(config)
    else:
      raise ConfigInitError()
  elif existing_datastore == "MySQLAdvancedDataStore":
    print("  MySQL Host: %s\n  MySQL Port: %s\n  MySQL Database: %s\n"
          "  MySQL Username: %s\n" %
          (grr_config.CONFIG.Get("Mysql.host"),
           grr_config.CONFIG.Get("Mysql.port"),
           grr_config.CONFIG.Get("Mysql.database_name"),
           grr_config.CONFIG.Get("Mysql.database_username")))
    if not RetryBoolQuestion("Do you want to keep this configuration?", True):
      ConfigureMySQLDatastore(config)


def ConfigureUrls(config):
  """Guides the user through configuration of various URLs used by GRR."""
  print("\n\n-=GRR URLs=-\n"
        "For GRR to work each client has to be able to communicate with the\n"
        "server. To do this we normally need a public dns name or IP address\n"
        "to communicate with. In the standard configuration this will be used\n"
        "to host both the client facing server and the admin user interface.\n")

  existing_ui_urn = grr_config.CONFIG.Get("AdminUI.url", default=None)
  existing_frontend_urns = grr_config.CONFIG.Get("Client.server_urls")
  if not existing_frontend_urns:
    # Port from older deprecated setting Client.control_urls.
    existing_control_urns = grr_config.CONFIG.Get(
        "Client.control_urls", default=None)
    if existing_control_urns is not None:
      existing_frontend_urns = []
      for existing_control_urn in existing_control_urns:
        if not existing_control_urn.endswith("control"):
          raise RuntimeError(
              "Invalid existing control URL: %s" % existing_control_urn)

        existing_frontend_urns.append(
            existing_control_urn.rsplit("/", 1)[0] + "/")

      config.Set("Client.server_urls", existing_frontend_urns)
      config.Set("Client.control_urls", ["deprecated use Client.server_urls"])

  if not existing_frontend_urns or not existing_ui_urn:
    ConfigureHostnames(config)
  else:
    print("Found existing settings:\n  AdminUI URL: %s\n  "
          "Frontend URL(s): %s\n" % (existing_ui_urn, existing_frontend_urns))
    if not RetryBoolQuestion("Do you want to keep this configuration?", True):
      ConfigureHostnames(config)


def ConfigureEmails(config):
  """Guides the user through email setup."""
  print("\n\n-=GRR Emails=-\n"
        "GRR needs to be able to send emails for various logging and\n"
        "alerting functions. The email domain will be appended to GRR\n"
        "usernames when sending emails to users.\n")

  existing_log_domain = grr_config.CONFIG.Get("Logging.domain", default=None)
  existing_al_email = grr_config.CONFIG.Get(
      "Monitoring.alert_email", default=None)
  existing_em_email = grr_config.CONFIG.Get(
      "Monitoring.emergency_access_email", default=None)
  if existing_log_domain and existing_al_email and existing_em_email:
    print("Found existing settings:\n"
          "  Email Domain: %s\n  Alert Email Address: %s\n"
          "  Emergency Access Email Address: %s\n" %
          (existing_log_domain, existing_al_email, existing_em_email))
    if RetryBoolQuestion("Do you want to keep this configuration?", True):
      return

  print("\n\n-=Monitoring/Email Domain=-\n"
        "Emails concerning alerts or updates must be sent to this domain.\n")
  domain = RetryQuestion("Email Domain e.g example.com",
                         "^([\\.A-Za-z0-9-]+)*$",
                         grr_config.CONFIG.Get("Logging.domain"))
  config.Set("Logging.domain", domain)

  print("\n\n-=Alert Email Address=-\n"
        "Address where monitoring events get sent, e.g. crashed clients, \n"
        "broken server, etc.\n")
  email = RetryQuestion("Alert Email Address", "", "grr-monitoring@%s" % domain)
  config.Set("Monitoring.alert_email", email)

  print("\n\n-=Emergency Email Address=-\n"
        "Address where high priority events such as an emergency ACL bypass "
        "are sent.\n")
  emergency_email = RetryQuestion("Emergency Access Email Address", "",
                                  "grr-emergency@%s" % domain)
  config.Set("Monitoring.emergency_access_email", emergency_email)


def ConfigureRekall(config):
  rekall_enabled = grr_config.CONFIG.Get("Rekall.enabled", False)
  if rekall_enabled:
    rekall_enabled = RetryBoolQuestion("Keep Rekall enabled?", True)
  else:
    rekall_enabled = RetryBoolQuestion(
        "Rekall is no longer actively supported. Enable anyway?", False)
  config.Set("Rekall.enabled", rekall_enabled)


def InstallTemplatePackage():
  """Call pip to install the templates."""
  virtualenv_bin = os.path.dirname(sys.executable)
  extension = os.path.splitext(sys.executable)[1]
  pip = "%s/pip%s" % (virtualenv_bin, extension)

  # Install the GRR server component to satisfy the dependency below.
  major_minor_version = ".".join(
      pkg_resources.get_distribution("grr-response-core").version.split(".")[0:
                                                                             2])
  # Note that this version spec requires a recent version of pip
  subprocess.check_call([
      sys.executable, pip, "install", "--upgrade", "-f",
      "https://storage.googleapis.com/releases.grr-response.com/index.html",
      "grr-response-templates==%s.*" % major_minor_version
  ])


def FinalizeConfigInit(config, token):
  """Performs the final steps of config initialization."""
  config.Set("Server.initialized", True)
  print("\nWriting configuration to %s." % config["Config.writeback"])
  config.Write()
  print("Initializing the datastore.")
  # Reload the config and initialize the GRR database.
  server_startup.Init()

  print("\nStep 3: Adding GRR Admin User")
  try:
    maintenance_utils.AddUser(
        "admin",
        labels=["admin"],
        token=token,
        password=flags.FLAGS.admin_password)
  except maintenance_utils.UserError:
    if flags.FLAGS.noprompt:
      maintenance_utils.UpdateUser(
          "admin",
          password=flags.FLAGS.admin_password,
          add_labels=["admin"],
          token=token)
    else:
      # pytype: disable=wrong-arg-count
      if ((builtins.input("User 'admin' already exists, do you want to "
                          "reset the password? [yN]: ").upper() or "N") == "Y"):
        maintenance_utils.UpdateUser(
            "admin", password=True, add_labels=["admin"], token=token)
      # pytype: enable=wrong-arg-count

  print("\nStep 4: Repackaging clients with new configuration.")
  redownload_templates = False
  repack_templates = False
  if flags.FLAGS.noprompt:
    redownload_templates = flags.FLAGS.redownload_templates
    repack_templates = not flags.FLAGS.norepack_templates
  else:
    redownload_templates = RetryBoolQuestion(
        "Server debs include client templates. Re-download templates?", False)
    repack_templates = RetryBoolQuestion("Repack client templates?", True)
  if redownload_templates:
    InstallTemplatePackage()
  # Build debug binaries, then build release binaries.
  if repack_templates:
    repacking.TemplateRepacker().RepackAllTemplates(upload=True, token=token)
  print("\nGRR Initialization complete! You can edit the new configuration "
        "in %s.\n" % config["Config.writeback"])
  print("Please restart the service for the new configuration to take "
        "effect.\n")


def Initialize(config=None, token=None):
  """Initialize or update a GRR configuration."""

  print("Checking write access on config %s" % config["Config.writeback"])
  if not os.access(config.parser.filename, os.W_OK):
    raise IOError("Config not writeable (need sudo?)")

  print("\nStep 0: Importing Configuration from previous installation.")
  options_imported = 0
  prev_config_file = config.Get("ConfigUpdater.old_config", default=None)
  if prev_config_file and os.access(prev_config_file, os.R_OK):
    print("Found config file %s." % prev_config_file)
    # pytype: disable=wrong-arg-count
    if builtins.input("Do you want to import this configuration?"
                      " [yN]: ").upper() == "Y":
      options_imported = ImportConfig(prev_config_file, config)
    # pytype: enable=wrong-arg-count
  else:
    print("No old config file found.")

  print("\nStep 1: Setting Basic Configuration Parameters")
  print("We are now going to configure the server using a bunch of questions.")
  ConfigureDatastore(config)
  ConfigureUrls(config)
  ConfigureEmails(config)
  ConfigureRekall(config)

  print("\nStep 2: Key Generation")
  if config.Get("PrivateKeys.server_key", default=None):
    if options_imported > 0:
      print("Since you have imported keys from another installation in the "
            "last step,\nyou probably do not want to generate new keys now.")
    # pytype: disable=wrong-arg-count
    if (builtins.input("You already have keys in your config, do you want to"
                       " overwrite them? [yN]: ").upper() or "N") == "Y":
      GenerateKeys(config, overwrite_keys=True)
    # pytype: enable=wrong-arg-count
  else:
    GenerateKeys(config)

  FinalizeConfigInit(config, token)


def InitializeNoPrompt(config=None, token=None):
  """Initialize GRR with no prompts.

  Args:
    config: config object
    token: auth token

  Raises:
    ValueError: if required flags are not provided, or if the config has
      already been initialized.
    IOError: if config is not writeable
    ConfigInitError: if GRR is unable to connect to a running MySQL instance.

  This method does the minimum work necessary to configure GRR without any user
  prompting, relying heavily on config default values. User must supply the
  external hostname, admin password, and MySQL password; everything else is set
  automatically.
  """
  if config["Server.initialized"]:
    raise ValueError("Config has already been initialized.")
  if not flags.FLAGS.external_hostname:
    raise ValueError(
        "--noprompt set, but --external_hostname was not provided.")
  if not flags.FLAGS.admin_password:
    raise ValueError("--noprompt set, but --admin_password was not provided.")
  if flags.FLAGS.mysql_password is None:
    raise ValueError("--noprompt set, but --mysql_password was not provided.")

  print("Checking write access on config %s" % config.parser)
  if not os.access(config.parser.filename, os.W_OK):
    raise IOError("Config not writeable (need sudo?)")

  config_dict = {}
  config_dict["Datastore.implementation"] = "MySQLAdvancedDataStore"
  config_dict["Mysql.host"] = (
      flags.FLAGS.mysql_hostname or config["Mysql.host"])
  config_dict["Mysql.port"] = (flags.FLAGS.mysql_port or config["Mysql.port"])
  config_dict["Mysql.database_name"] = (
      flags.FLAGS.mysql_db or config["Mysql.database_name"])
  config_dict["Mysql.database_username"] = (
      flags.FLAGS.mysql_username or config["Mysql.database_username"])
  hostname = flags.FLAGS.external_hostname
  config_dict["Client.server_urls"] = [
      "http://%s:%s/" % (hostname, config["Frontend.bind_port"])
  ]

  config_dict["AdminUI.url"] = "http://%s:%s" % (hostname,
                                                 config["AdminUI.port"])
  config_dict["Logging.domain"] = hostname
  config_dict["Monitoring.alert_email"] = "grr-monitoring@%s" % hostname
  config_dict["Monitoring.emergency_access_email"] = (
      "grr-emergency@%s" % hostname)
  config_dict["Rekall.enabled"] = flags.FLAGS.enable_rekall
  # Print all configuration options, except for the MySQL password.
  print("Setting configuration as:\n\n%s" % config_dict)
  config_dict["Mysql.database_password"] = flags.FLAGS.mysql_password
  if CheckMySQLConnection(config_dict):
    print("Successfully connected to MySQL with the given configuration.")
  else:
    print("Error: Could not connect to MySQL with the given configuration.")
    raise ConfigInitError()
  for key, value in iteritems(config_dict):
    config.Set(key, value)
  GenerateKeys(config)
  FinalizeConfigInit(config, token)


def UploadRaw(file_path, aff4_path, token=None):
  """Upload a file to the datastore."""
  full_path = rdfvalue.RDFURN(aff4_path).Add(os.path.basename(file_path))
  fd = aff4.FACTORY.Create(full_path, "AFF4Image", mode="w", token=token)
  fd.Write(open(file_path, "rb").read(1024 * 1024 * 30))
  fd.Close()
  return str(fd.urn)


def GetToken():
  # Extend for user authorization
  # SetUID is required to create and write to various aff4 paths when updating
  # config.
  return access_control.ACLToken(username="GRRConsole").SetUID()
