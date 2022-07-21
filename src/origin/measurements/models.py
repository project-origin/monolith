import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.orm import relationship

from origin.db import ModelBase
from origin.meteringpoints import MeteringPointType


class Measurement(ModelBase):
    """
    Implementation of a single measurement that has been measured
    by a MeteringPoint. It consists of a period of time (defined by its
    begin) along with the amount of energy produced or consumed
    in Wh (Watts per hour). The type of measurement (production or
    consumption) depends on the MeteringPoint. Only one measurement can
    exists per MeteringPoint per begin.

    Measurements of type PRODUCTION also has a GGO issued to it.
    """
    __tablename__ = 'measurement'
    __table_args__ = (
        sa.UniqueConstraint('gsrn', 'begin'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, index=True)

    # Time when measurement was imported from ElOverblik / inserted to DB
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    gsrn = sa.Column(sa.String(), sa.ForeignKey('meteringpoint.gsrn'), index=True, nullable=False)
    begin: datetime = sa.Column(sa.DateTime(timezone=True), index=True, nullable=False)
    end: datetime = sa.Column(sa.DateTime(timezone=True), nullable=False)
    amount = sa.Column(sa.Integer(), nullable=False)

    meteringpoint = relationship('MeteringPoint', foreign_keys=[gsrn], lazy='joined')

    def __str__(self):
        return 'Measurement<%s>' % ', '.join((
            f'gsrn={self.gsrn}',
            f'begin={self.begin}',
            f'amount={self.amount}',
        ))

    @property
    def sub(self):
        """
        Returns the subject who owns the MeteringPoint which this
        measurement belongs to (ie. user ID).

        :rtype: str
        """
        return self.meteringpoint.sub

    @property
    def sector(self):
        """
        Returns the sector (Price area) of the MeteringPoint which this
        measurement belongs to.

        :rtype: str
        """
        return self.meteringpoint.sector

    @property
    def technology_code(self):
        """
        Returns the technology code of the MeteringPoint which this
        measurement belongs to.

        :rtype: str
        """
        return self.meteringpoint.technology_code

    @property
    def fuel_code(self):
        """
        Returns the fuel code of the MeteringPoint which this
        measurement belongs to.

        :rtype: str
        """
        return self.meteringpoint.fuel_code

    @property
    def type(self):
        """
        Returns the type og measurement, ie. PRODUCTION or CONSUMPTION.

        :rtype: MeteringPointType
        """
        return self.meteringpoint.type

    @property
    def is_production(self):
        """
        Returns True if this is a production measurement.

        :rtype: bool
        """
        return self.meteringpoint.type is MeteringPointType.PRODUCTION
