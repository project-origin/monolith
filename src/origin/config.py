import os
from decouple import config
from datetime import datetime, timezone, timedelta


__current_file = os.path.abspath(__file__)
__current_folder = os.path.split(__current_file)[0]


# -- Directories -------------------------------------------------------------

# Project root
ROOT_DIR = os.path.abspath(os.path.join(__current_folder, '..', '..'))

# Source
SOURCE_DIR = os.path.join(ROOT_DIR, 'src')

# Migrations
MIGRATIONS_DIR = os.path.join(SOURCE_DIR, 'migrations')
ALEMBIC_CONFIG_PATH = os.path.join(MIGRATIONS_DIR, 'alembic.ini')


# -- General -----------------------------------------------------------------

# Name of project
PROJECT_NAME = config('PROJECT_NAME', default='Project Origin')

# Private secret (hashing/salting etc.)
SECRET = config('SECRET')


# -- General -----------------------------------------------------------------

# Enable/disable debug mode
DEBUG = config('DEBUG', default=False, cast=bool)

# Service port (when running development server)
DEVELOP_HOST = config('DEVELOP_HOST', default='0.0.0.0')

# Service port (when running development server)
DEVELOP_PORT = config('DEVELOP_PORT', default=8081, cast=int)

# Service absolute URL (when running development server)
DEVELOP_URL = f'http://{DEVELOP_HOST}:{DEVELOP_PORT}'

# URL to frontend (public accessible)
FRONTEND_URL = config('FRONTEND_URL')

# URL to backend (public accessible)
BACKEND_URL = config('BACKEND_URL', default=DEVELOP_URL)

# CORS origins
CORS_ORIGINS = config('CORS_ORIGINS')


# -- SQL Database ------------------------------------------------------------

SQL_ALCHEMY_SETTINGS = {
    'echo': False,
    'pool_pre_ping': True,
    'pool_size': config('DATABASE_CONN_POLL_SIZE', default=3),
}

SQL_DATABASE_URI = config('SQL_DATABASE_URI')


# -- webhook -----------------------------------------------------------------

HMAC_HEADER = config('HMAC_HEADER', default='x-hub-signature')


# -- Auth/tokens -------------------------------------------------------------

TOKEN_HEADER = 'Authorization'


# -- Email -------------------------------------------------------------------

EMAIL_FROM_NAME = config('EMAIL_FROM_NAME')
EMAIL_FROM_ADDRESS = config('EMAIL_FROM_ADDRESS')
EMAIL_TO_ADDRESS = config('EMAIL_TO_ADDRESS')
EMAIL_PREFIX = config('EMAIL_PREFIX')
SENDGRID_API_KEY = config('SENDGRID_API_KEY')

SEND_AGREEMENT_INVITATION_EMAIL = config(
    'SEND_AGREEMENT_INVITATION_EMAIL', cast=bool, default=True)


# -- Misc --------------------------------------------------------------------

GGO_EXPIRE_TIME = timedelta(days=config('GGO_EXPIRE_TIME', default=90))
GGO_ISSUE_INTERVAL = timedelta(minutes=config('GGO_ISSUE_INTERVAL', default=60))

UNKNOWN_TECHNOLOGY_LABEL = 'Unknown'

# Used when debugging for importing test data
if os.environ.get('FIRST_MEASUREMENT_TIME'):
    FIRST_MEASUREMENT_TIME = datetime\
        .strptime(config('FIRST_MEASUREMENT_TIME'), '%Y-%m-%dT%H:%M:%SZ') \
        .astimezone(timezone.utc)
else:
    FIRST_MEASUREMENT_TIME = None

if os.environ.get('LAST_MEASUREMENT_TIME'):
    LAST_MEASUREMENT_TIME = datetime\
        .strptime(config('LAST_MEASUREMENT_TIME'), '%Y-%m-%dT%H:%M:%SZ') \
        .astimezone(timezone.utc)
else:
    LAST_MEASUREMENT_TIME = None
