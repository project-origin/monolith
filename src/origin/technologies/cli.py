import csv
import requests
from click import Abort, echo
from cloup import group, command, option_group, option, Path
from cloup.constraints import RequireExactly

from origin.db import atomic
from origin.auth import UserQuery

from .models import Technology


# -- Commands ----------------------------------------------------------------


@command()
@option_group(
    'CSV file source',
    option(
        '--path',
        type=Path(file_okay=True, dir_okay=False, exists=True, resolve_path=True),
        help='Local path to CSV file',
    ),
    option(
        '--url',
        type=str,
        help='URL to CSV file',
    ),
    constraint=RequireExactly(1),
)
@atomic
def import_meteringpoints(session, path, url):
    """
    Import technologies from CSV file. The file must contain appropriate
    headers in the first line.

    CSV example:

        tech_code,fuel_code,technology
        T010101,F01010101,Wind
        T020202,F02020202,Solar
    """
    if path:
        f = open(path, 'r')
        lines = iter(f)
    elif url:
        r = requests.get(url)
        lines = map(lambda z: z.decode(), r.iter_lines())
    else:
        raise RuntimeError('Should NOT have happened')

    for t in csv.DictReader(lines):
        session.add(Technology(
            technology=t['technology'],
            tech_code=t['tech_code'],
            fuel_code=t['fuel_code'],
        ))
        session.flush()


# -- Group -------------------------------------------------------------------


@group()
def technologies_group() -> None:
    """
    Manage technologies
    """
    pass


technologies_group.add_command(import_meteringpoints, "import")
