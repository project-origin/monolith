import sqlalchemy as sa

from origin.db import ModelBase


class Technology(ModelBase):
    """
    A technology (by label) consists of a combination
    of technology_code and fuel_code.
    """
    __tablename__ = 'technology'
    __table_args__ = (
        sa.UniqueConstraint('tech_code', 'fuel_code'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, index=True)
    technology = sa.Column(sa.String(), nullable=False)
    tech_code = sa.Column(sa.String(), nullable=False)
    fuel_code = sa.Column(sa.String(), nullable=False)
