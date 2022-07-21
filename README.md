![alt text](doc/logo.png)

# Project Origin backend (merged into a monolith)

This is the revisioned backend to Project Origin. Its a merge between the old
DataHub service, Account service, and Example Backend into one project/service.
It supports roughly the same API interface and Example Backend, so the frontend
can _almost_ use the two backends interchangeably. Its only external dependency
is a PostgreSQL server.

This projects exposes a command-line interface for developers to interact with it.
More details later in this document.



---




# Building and running production-ready Docker image

Start by locking dependencies (if necessary):

    pipenv lock -r > requirements.txt

Then build the Docker image:

    docker build -t origin:XX .

## Running container images

Web API:

    docker run origin:XX




---




# Configuration

The service needs a number of configuration options for it to run.
Options can be defined in either of the following ways (in prioritized order):

- Environment variables
- Defined in files `settings.ini` or `.env`
- Command line arguments

For example, if an option is defined as an environment variable, it will be
used. Otherwise, the system looks towards the value in the `settings.ini` or
`env.ini` (not both), and so on.

When running the service locally for development and debugging, most of the
necessary options are defined in `settings.ini`. The remaining (secret) options
should be defined as environment variables, thus not committed to Git by accident.

## Environment variables

See src/origin/config.py for details.

Name | Description                                                   | Example
:--- |:--------------------------------------------------------------| :--- |
`DEBUG` | Whether or not to enable debugging mode (off by default)      | `0` or `1`
`SECRET` | Application secret for misc. operations                       | `foobar`
`FRONTEND_URL` | Public URL the the frontend application                       | `https://projectorigin.dk`
`BACKEND_URL` | Public URL the the backend application                        | `https://be.projectorigin.dk`
`CORS_ORIGINS` | Allowed CORS origins                                          | `http://www.example.com`
**SQL database:** |       
`SQL_DATABASE_URI` | Database connection string for SQLAlchemy                     | `postgresql://scott:tiger@localhost/mydatabase`
`DATABASE_CONN_POLL_SIZE` | Connection pool size per container                            | `10`
**E-mail:** |                                                               |
`EMAIL_FROM_NAME` | From-name in outgoing e-mails                                 | `John Doe`
`EMAIL_FROM_ADDRESS` | From-address in outgoing e-mails                              | `john@doe.com`
`EMAIL_TO_ADDRESS` | SendGrid API key                                              | `support@energinet.dk`
`EMAIL_PREFIX` | SendGrid API key                                              | `eloverblik - `
`SENDGRID_API_KEY` | SendGrid API key                                              | `foobar`




---




# SQL Database

The services make use [SQLAlchemy](https://www.sqlalchemy.org/) to connect and
interact with an SQL database. The underlying SQL server technology is of less
importance, as [SQLAlchemy supports a variety of databases](https://docs.sqlalchemy.org/en/14/core/engines.html),
even SQLite for development and debugging. One note, however, is that the
underlying driver for specific databases must be installed (via Pip/Pipfile).
Currently, only the PostgreSQL is installed.

## Connecting to database

The services require the `SQL_URI` configuration option, which must be
[in a format SQLAlchemy supports](https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls).

## Managing database migrations

The services make use of [Alembic](https://alembic.sqlalchemy.org/en/latest/)
to manage database migrations, since this feature is not build into SQLAlchemy
itself.

To create a new database revision:

    $ cd src/
    $ alembic --config=migrations/alembic.ini revision --autogenerate

To apply all existing database migrations, thus upgrading the database to the latest scheme:

    $ cd src/
    $ alembic --config=migrations/alembic.ini upgrade head

## Applying migrations in production

When starting the services through their respective entrypoints, the first thing
they do is apply migrations.





---




## Building and running container image

    docker build -f Dockerfile -t origin:v1 .
    docker run origin:v1


# Installing and running the project

The following sections describes how to install and run the project locally for development and debugging.

### Requirements

- Python 3.7
- Pip
- Pipenv

### First time installation

Make sure to upgrade your system packages for good measure:
   
    pip install --upgrade --user setuptools pip pipenv

Then install project dependencies:

    pipenv install
   
Then apply database migrations (while at the same time creating an empty SQLite database-file, if using SQLite):

    cd src/migrations
    pipenv run alembic upgrade head
    cd ../../

Then (optionally) seed the database with some data:

    pipenv run python src/seed.py

### Running locally (development)

This starts the local development server (NOT for production use):

    cd src
    pipenv run python -m origin debug






---



# Command-line interface

This projects exposes a command-line interface for developers to interact with it.
It supports these features (among other):

- Run debug/development API
- Users/auth:
  - List/export users (to CSV or JSON)
  - Create user
  - Delete user
  - Activate/deactivate user
  - Issue API token on behalf of user (for testing/debug)
- MeteringPoints:
  - List/export meteringpoints (to CSV or JSON)
  - Create meteringpoint
  - Import meteringpoints from CSV (from filesystem or public URL)
- Measurements:
  - Import measurements from CSV (from filesystem or public URL)
  - Auto-generate measurements (for easy testing)
- Technologies
  - Import technologies (tech- and fuel-code combinations) (from filesystem or public URL)

To access the CLI:

    cs src
    pipenv run python -m origin
