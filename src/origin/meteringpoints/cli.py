import csv
import json
import sys

import requests
from click import Abort, echo
from cloup import group, command, option_group, option, Path, Choice
from cloup.constraints import RequireExactly

from origin.auth import UserQuery
from origin.db import atomic, inject_session
from . import MeteringPointQuery

from .models import MeteringPoint, MeteringPointType


# -- Commands ----------------------------------------------------------------


@command()
@option(
    '--out',
    type=Choice(('csv', 'json')),
    required=True,
    default='json',
    help='Output format',
)
@inject_session
def list_meteringpoints(out, session):
    """
    List meteringpoints
    """
    meteringpoints = MeteringPointQuery(session).all()

    keys = (
        'gsrn',
        'type',
        'sector',
        'tech_code',
        'fuel_code',
        'technology_label',
        'subject',
    )

    objects = [
        {key: getattr(mp, key) for key in keys}
        for mp in meteringpoints
    ]

    if out == 'csv':
        writer = csv.DictWriter(
            sys.stdout, extrasaction='ignore', fieldnames=keys)
        writer.writeheader()
        writer.writerows(objects)

    elif out == 'json':
        print(json.dumps(objects, indent=4, sort_keys=True, default=str))


@command()
@option(
    '--subject',
    type=str,
    required=True,
    prompt=True,
    help='User (subject) to own the MeteringPoint',
)
@option(
    '--gsrn',
    type=str,
    required=True,
    prompt=True,
    help='GSRN number',
)
@option(
    '--type',
    type=Choice([e.value for e in MeteringPointType]),
    required=True,
    prompt=True,
    default='Type',
)
@option(
    '--sector',
    type=str,
    required=True,
    prompt=True,
    help='Sector',
)
@option(
    '--tech',
    type=str,
    required=False,
    default=None,
    prompt=True,
    help='Technology code (if production)',
)
@option(
    '--fuel',
    type=str,
    required=False,
    default=None,
    prompt=True,
    help='Fuel code (if production)',
)
@atomic
def create_meteringpoint(subject, gsrn, type, sector, tech, fuel, session):
    """
    Create a new meteringpoint
    """
    actual_type = MeteringPointType(type)

    if actual_type is MeteringPointType.PRODUCTION:
        if tech is None:
            echo('Technology code is required for production meteringpoints')
            raise Abort()
        if fuel is None:
            echo('Fuel code is required for production meteringpoints')
            raise Abort()

    session.add(MeteringPoint(
        subject=subject,
        gsrn=gsrn,
        type=actual_type,
        sector=sector,
        tech_code=tech,
        fuel_code=fuel,
    ))


@command()
@option(
    '--subject',
    type=str,
    required=True,
    prompt=True,
    help='User subject to add meteringpoints to',
)
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
def import_meteringpoints(session, subject, path, url):
    """
    Import meteringpoints from CSV file. The file must contain appropriate
    headers in the first line.

    CSV example:

        gsrn,type,sector,tech_code,fuel_code
        123456789012345,production,T010101,F01010101
        543210987654321,consumption,,
    """
    user = UserQuery(session) \
        .has_subject(subject) \
        .one_or_none()

    if user is None:
        echo(f'User with subject does not exist: {subject}')
        raise Abort()

    if path:
        f = open(path, 'r')
        lines = iter(f)
    elif url:
        r = requests.get(url)
        lines = map(lambda z: z.decode(), r.iter_lines())
    else:
        raise RuntimeError('Should NOT have happened')

    for mp in csv.DictReader(lines):
        meteringpoint = MeteringPoint(
            user=user,
            gsrn=mp['gsrn'],
            sector=mp['sector'],
            type=MeteringPointType(mp['type']),
            tech_code=mp.get('tech_code') or None,
            fuel_code=mp.get('fuel_code') or None,
        )

        session.add(meteringpoint)
        session.flush()


# -- Group -------------------------------------------------------------------


@group()
def meteringpoints_group() -> None:
    """
    Manage meteringpoints
    """
    pass


meteringpoints_group.add_command(create_meteringpoint, "create")
meteringpoints_group.add_command(import_meteringpoints, "import")
meteringpoints_group.add_command(list_meteringpoints, "list")
