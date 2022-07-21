import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from uuid import uuid4
from enum import Enum

from origin.db import ModelBase
from origin.auth import User
from origin.common import Unit


class AgreementDirection(Enum):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'


class AgreementState(Enum):
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    DECLINED = 'DECLINED'
    CANCELLED = 'CANCELLED'
    WITHDRAWN = 'WITHDRAWN'


class TradeAgreement(ModelBase):
    """
    TODO
    """
    __tablename__ = 'agreements_agreement'
    __table_args__ = (
        sa.UniqueConstraint('public_id'),
        sa.CheckConstraint(
            "(amount_percent IS NULL) OR (amount_percent >= 1 AND amount_percent <= 100)",
            name="amount_percent_is_NULL_or_between_1_and_100",
        ),
        sa.CheckConstraint(
            "(limit_to_consumption = 'f' and amount is not null and unit is not null) or (limit_to_consumption = 't')",
            name="limit_to_consumption_OR_amount_and_unit",
        ),
    )

    # Meta
    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True, index=True)
    public_id = sa.Column(sa.String(), index=True, nullable=False)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    declined = sa.Column(sa.DateTime(timezone=True))
    cancelled = sa.Column(sa.DateTime(timezone=True))

    # Involved parties (users)
    user_proposed_subject = sa.Column(sa.String(), sa.ForeignKey('user.subject'), index=True, nullable=False)
    user_proposed = relationship('User', foreign_keys=[user_proposed_subject], lazy='joined')
    user_from_subject = sa.Column(sa.String(), sa.ForeignKey('user.subject'), index=True, nullable=False)
    user_from = relationship('User', foreign_keys=[user_from_subject], lazy='joined')
    user_to_subject = sa.Column(sa.String(), sa.ForeignKey('user.subject'), index=True, nullable=False)
    user_to = relationship('User', foreign_keys=[user_to_subject], lazy='joined')

    # Outbound facilities
    facility_gsrn = sa.Column(ARRAY(sa.Integer()))

    # Agreement details
    state = sa.Column(sa.Enum(AgreementState), index=True, nullable=False)
    date_from = sa.Column(sa.Date(), nullable=False)
    date_to = sa.Column(sa.Date(), nullable=False)
    technologies = sa.Column(ARRAY(sa.String()), index=True)
    reference = sa.Column(sa.String())

    # Max. amount to transfer (per begin)
    amount = sa.Column(sa.Integer())
    unit = sa.Column(sa.Enum(Unit))

    # Transfer percentage (though never exceed max. amount - "amount" above)
    amount_percent = sa.Column(sa.Integer())

    # Limit transferred amount to recipient's consumption?
    limit_to_consumption = sa.Column(sa.Boolean())

    # Lowest number = highest priority
    # Is set when user accepts the agreement, otherwise None
    transfer_priority = sa.Column(sa.Integer())

    # Senders proposal note to recipient
    proposal_note = sa.Column(sa.String())

    @property
    def user_proposed_to(self):
        """
        :rtype: User
        """
        if self.user_from_subject == self.user_proposed_subject:
            return self.user_to
        else:
            return self.user_from

    @property
    def transfer_reference(self):
        """
        :rtype: str
        """
        return self.public_id

    @property
    def calculated_amount(self):
        """
        :rtype: int
        """
        return self.amount * self.unit.value

    def is_proposed_by(self, user):
        """
        :param User user:
        :rtype: bool
        """
        return user.subject == self.user_proposed_subject

    def is_inbound_to(self, user):
        """
        :param User user:
        :rtype: bool
        """
        return user.subject == self.user_to_subject

    def is_outbound_from(self, user):
        """
        :param User user:
        :rtype: bool
        """
        return user.subject == self.user_from_subject

    def is_pending(self):
        """
        :rtype: bool
        """
        return self.state == AgreementState.PENDING

    def decline_proposal(self):
        self.state = AgreementState.DECLINED
        self.declined = func.now()

    def cancel(self):
        self.state = AgreementState.CANCELLED
        self.cancelled = func.now()
        self.transfer_priority = None

# ----------------------------------------------------------------------------


@sa.event.listens_for(TradeAgreement, 'before_insert')
def on_before_creating_task(mapper, connect, agreement):
    if not agreement.public_id:
        agreement.public_id = str(uuid4())
