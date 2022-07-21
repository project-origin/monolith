import logging
from flask import Flask
from flask_cors import CORS
# from opencensus.trace import config_integration
# from opencensus.ext.flask.flask_middleware import FlaskMiddleware

from .urls import urls
# from .logger import handler, exporter, sampler
from .config import SECRET, CORS_ORIGINS, PROJECT_NAME, DEBUG

# Import models here for SQLAlchemy to detech them
from .models import VERSIONED_DB_MODELS


# -- Flask setup -------------------------------------------------------------

app = Flask(PROJECT_NAME)
app.config['SECRET_KEY'] = SECRET
app.config['PROPAGATE_EXCEPTIONS'] = DEBUG

cors = CORS(app, resources={r'*': {'origins': CORS_ORIGINS}})


# -- URLs/routes setup -------------------------------------------------------

for url, controller in urls:
    app.add_url_rule(url, url, controller, methods=[controller.METHOD])
