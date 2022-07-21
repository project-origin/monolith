import click

from .app import app
from .config import DEVELOP_HOST, DEVELOP_PORT
from .auth import users_group
from .measurements.cli import measurements_group
from .meteringpoints import meteringpoints_group
from .technologies import technologies_group


# -- Development server-------------------------------------------------------


@click.command()
@click.option(
    "--host",
    "host",
    required=False,
    default=DEVELOP_HOST,
    type=str,
    help="Host to serve on",
)
@click.option(
    "--port",
    "port",
    required=False,
    default=DEVELOP_PORT,
    type=str,
    help="Port to serve on",
)
def debug(host, port):
    """
    Run Web API debug/development server
    """
    app.run(host=host, port=port)


# -- Main --------------------------------------------------------------------


@click.group()
def main():
    """
    Project Origin CLI
    """
    pass


main.add_command(debug, "debug")
main.add_command(measurements_group, "measurements")
main.add_command(meteringpoints_group, "meteringpoints")
main.add_command(technologies_group, "technologies")
main.add_command(users_group, "users")
