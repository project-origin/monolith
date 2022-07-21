import csv
import random
import requests
from datetime import datetime, timezone
from click import echo, Abort
from cloup import group, command, option_group, option, Path, DateTime
from cloup.constraints import RequireExactly

from origin.db import atomic
from origin.config import GGO_ISSUE_INTERVAL
from origin.processes import create_measurement
from origin.meteringpoints import MeteringPointQuery


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
def import_measurements(session, path, url):
    """
    Import measurements from CSV file. The file must contain appropriate
    headers in the first line.

    CSV example:

        gsrn,begin,end,amount

        123456789012345,"2022-01-18T08:00:00+00:00","2022-01-18T09:00:00+00:00",1000

        543210987654321,"2022-01-18T08:00:00+00:00","2022-01-18T09:00:00+00:00",2000
    """
    if path:
        f = open(path, 'r')
        lines = iter(f)
    elif url:
        r = requests.get(url)
        lines = map(lambda z: z.decode(), r.iter_lines())
    else:
        raise RuntimeError('Should NOT have happened')

    meteringpoints = {}

    def __get_meteringpoint(gsrn):
        if gsrn not in meteringpoints:
            meteringpoints[gsrn] = MeteringPointQuery(session) \
                .has_gsrn(m['gsrn']) \
                .one_or_none()

            if meteringpoints[gsrn] is None:
                echo(f'Meteringpoint with GSRN f"{gsrn}" not found')
                raise Abort()
        return meteringpoints[gsrn]

    for m in csv.DictReader(lines):
        begin = datetime.fromisoformat(m['begin'])
        end = datetime.fromisoformat(m['end'])
        amount = int(m['amount'])
        mp = __get_meteringpoint(m['gsrn'])

        create_measurement(
            meteringpoint=mp,
            begin=begin,
            end=end,
            amount=amount,
            session=session,
        )


@command()
@option(
    '--gsrn',
    type=str,
    required=True,
    prompt=True,
    help='GSRN number',
)
@option(
    '--from',
    'from_',
    type=DateTime(formats=['%Y-%m-%d %H:%M']),
    required=True,
    prompt=True,
    help='Begin from (included)',
)
@option(
    '--to',
    'to_',
    type=DateTime(formats=['%Y-%m-%d %H:%M']),
    required=True,
    prompt=True,
    help='Begin to (excluded)',
)
@option(
    '--min',
    'min_',
    type=int,
    required=True,
    prompt=True,
    help='Minimum random value per measurement',
)
@option(
    '--max',
    'max_',
    type=int,
    required=True,
    prompt=True,
    help='Maximum random value per measurement',
)
@atomic
def generate_measurements(gsrn, from_, to_, min_, max_, session):
    """
    Autogenerate new measurements using randomized amount
    """
    mp = MeteringPointQuery(session) \
        .has_gsrn(gsrn) \
        .one_or_none()

    if mp is None:
        echo(f'Meteringpoint with GSRN f"{gsrn}" not found')
        raise Abort()

    begin = from_.astimezone(timezone.utc)
    end = to_.astimezone(timezone.utc)

    while begin < end:
        create_measurement(
            meteringpoint=mp,
            begin=begin,
            end=(begin + GGO_ISSUE_INTERVAL),
            amount=random.randint(min_, max_),
            session=session,
        )

        begin += GGO_ISSUE_INTERVAL


# -- Group -------------------------------------------------------------------


@group()
def measurements_group() -> None:
    """
    Manage measurements
    """
    pass


measurements_group.add_command(import_measurements, 'import')
measurements_group.add_command(generate_measurements, 'generate')
