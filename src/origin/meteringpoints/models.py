import sqlalchemy as sa
from dataclasses import dataclass, field
from sqlalchemy.orm import relationship
from typing import List
from uuid import uuid4
from enum import Enum

from origin.db import ModelBase


@dataclass
class MeteringPointFilters:
    type: str = field(default=None, metadata=dict(data_key='facilityType'))
    gsrn: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    technology: str = field(default=None)
    text: str = field(default=None)


class MeteringPointType(Enum):
    PRODUCTION = 'production'
    CONSUMPTION = 'consumption'


class MeteringPoint(ModelBase):
    """
    Implementation of a single MeteringPoint that belongs to a user
    identified by their subject (sub).
    """
    __tablename__ = 'meteringpoint'
    __table_args__ = (
        sa.UniqueConstraint('gsrn'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, index=True)
    public_id = sa.Column(sa.String(), index=True)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    gsrn = sa.Column(sa.String(), index=True, nullable=False)
    type: MeteringPointType = sa.Column(sa.Enum(MeteringPointType), index=True, nullable=False)
    sector = sa.Column(sa.String(), index=True, nullable=False)
    tech_code = sa.Column(sa.String())
    fuel_code = sa.Column(sa.String())
    name = sa.Column(sa.String(), nullable=False)

    # Lowest number = highest priority
    retiring_priority = sa.Column(sa.Integer())

    # Physical location
    street_code = sa.Column(sa.String())
    street_name = sa.Column(sa.String())
    building_number = sa.Column(sa.String())
    city_name = sa.Column(sa.String())
    postcode = sa.Column(sa.String())
    municipality_code = sa.Column(sa.String())

    # Relationships
    technology = relationship(
        'Technology',
        lazy='joined',
        primaryjoin=(
            'and_('
            'foreign(MeteringPoint.tech_code) == Technology.tech_code, '
            'foreign(MeteringPoint.fuel_code) == Technology.fuel_code'
            ')'
        ),
    )

    subject = sa.Column(
        sa.String(),
        sa.ForeignKey('user.subject'), index=True, nullable=False,
    )

    user = relationship('User', foreign_keys=[subject], lazy='joined')
    tags = relationship('MeteringPointTag', back_populates='meteringpoint', lazy='joined', cascade='all, delete-orphan')

    def is_producer(self):
        """
        Returns True if this meteringpoint is an energy producer.

        :rtype: bool
        """
        return self.type is MeteringPointType.PRODUCTION

    def is_consumer(self):
        """
        Returns True if this meteringpoint is an energy consumer.

        :rtype: bool
        """
        return self.type is MeteringPointType.CONSUMPTION

    @property
    def technology_label(self):
        """
        :rtype: str
        """
        return self.technology.technology if self.technology is not None else None


class MeteringPointTag(ModelBase):
    """
    TODO
    """
    __tablename__ = 'meteringpoint_tag'
    __table_args__ = (
        sa.UniqueConstraint('meteringpoint_id', 'tag'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True, index=True)
    meteringpoint_id = sa.Column(sa.Integer(), sa.ForeignKey('meteringpoint.id'), index=True, nullable=False)
    meteringpoint = relationship('MeteringPoint', foreign_keys=[meteringpoint_id], back_populates='tags')
    tag = sa.Column(sa.String(), index=True, nullable=False)


# -- Events ------------------------------------------------------------------


@sa.event.listens_for(MeteringPoint, 'before_insert')
def on_before_creating_task(mapper, connect, meteringpoint):
    if not meteringpoint.public_id:
        meteringpoint.public_id = str(uuid4())
    if not meteringpoint.name:
        meteringpoint.name = meteringpoint.gsrn
