from datetime import datetime, timezone

from origin.ggo.models import Ggo
from origin.measurements import Measurement
from origin.meteringpoints import MeteringPointType

from .consume_ggos import handle_ggo_received


# -- Helpers -----------------------------------------------------------------


def create_measurement(meteringpoint, begin, end, amount, session):
    """
    Create a new measurement in the system.

    If this is a production meteringpoint, this function also:
    - Issues a new GGO
    - Triggers consumption of said GGO (retire and/or transfer via agreement)

    :param origin.meteringpoints.MeteringPoint meteringpoint:
    :param datetime begin:
    :param datetime end:
    :param int amount:
    :param sqlalchemy.orm.Session session:
    """
    assert amount > 0, 'Amount has to be > 0'

    measurement = Measurement(
        meteringpoint=meteringpoint,
        begin=begin.astimezone(timezone.utc),
        end=end.astimezone(timezone.utc),
        amount=amount,
    )

    # Issue Measurement
    session.add(measurement)

    # Issue GGO (if production meteringpoint)
    if meteringpoint.type is MeteringPointType.PRODUCTION:
        ggo = Ggo.from_measurement(measurement)

        session.add(ggo)

        handle_ggo_received(ggo, session)
