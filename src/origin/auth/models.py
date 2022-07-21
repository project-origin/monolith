from uuid import uuid4

import sqlalchemy as sa

from origin.db import ModelBase


class User(ModelBase):
    """
    Represents one used in the system who is able to authenticate.
    """
    __tablename__ = 'user'
    __table_args__ = (
        sa.PrimaryKeyConstraint('subject'),
        sa.UniqueConstraint('subject'),
        sa.UniqueConstraint('email'),
    )

    subject = sa.Column(
        sa.String(), primary_key=True, index=True, nullable=False)
    created = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now())
    active = sa.Column(sa.Boolean(), default=False, nullable=False)

    # Details
    email = sa.Column(sa.String(), index=True, nullable=False)
    phone = sa.Column(sa.String(), index=True)
    password = sa.Column(sa.String(), nullable=False)
    name = sa.Column(sa.String(), nullable=False)
    company = sa.Column(sa.String(), nullable=False)

# ----------------------------------------------------------------------------


@sa.event.listens_for(User, 'before_insert')
def on_before_creating_task(mapper, connect, user):
    if not user.subject:
        user.subject = str(uuid4())

