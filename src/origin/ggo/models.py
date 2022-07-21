from enum import Enum
from uuid import uuid4

import sqlalchemy as sa
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.dialects.postgresql import JSONB

from origin.config import GGO_EXPIRE_TIME
from origin.db import ModelBase, Session


class Ggo(ModelBase):
    """
    Implementation of a single GGO that has been issued.

    GGOs are issued for all production MeteringPoints. Each individual
    Measurement from these MeteringPoints have a corresponding GGO with
    the same properties as the Measurement (begin/end, amount, technology..)
    """
    __tablename__ = 'ggo'
    __table_args__ = (
        sa.UniqueConstraint('measurement_id'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, index=True)
    public_id = sa.Column(sa.String(), index=True, nullable=False)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    issue_time = sa.Column(sa.DateTime(timezone=True), nullable=False)
    expire_time = sa.Column(sa.DateTime(timezone=True), nullable=False)
    begin = sa.Column(sa.DateTime(timezone=True), nullable=False, index=True)
    end = sa.Column(sa.DateTime(timezone=True), nullable=False)
    amount = sa.Column(sa.Integer(), nullable=False)
    sector = sa.Column(sa.String(), nullable=False, index=True)

    parent_id = sa.Column(sa.Integer(), sa.ForeignKey('ggo.id'), index=True)
    parent = relationship('Ggo', foreign_keys=[parent_id], remote_side=[id], uselist=False)

    measurement_id = sa.Column(sa.Integer(), sa.ForeignKey('measurement.id'), index=True)
    measurement = relationship('Measurement', foreign_keys=[measurement_id])

    subject = sa.Column(sa.String(), sa.ForeignKey('user.subject'), index=True, nullable=False)
    user = relationship('User', foreign_keys=[subject], lazy='joined')

    tech_code = sa.Column(sa.String())
    fuel_code = sa.Column(sa.String())
    technology = relationship(
        'Technology',
        lazy='joined',
        primaryjoin=(
            'and_('
            'foreign(Ggo.tech_code) == Technology.tech_code, '
            'foreign(Ggo.fuel_code) == Technology.fuel_code'
            ')'
        ),
    )

    # Whether or not this GGO was originally issued (False means its
    # product of a trade/split)
    issued = sa.Column(sa.Boolean(), nullable=False, index=True, default=False)

    # Whether or not this GGO is currently stored (False means its
    # been transferred, split or retired)
    stored = sa.Column(sa.Boolean(), nullable=False, index=True, default=False)

    # Whether or not this GGO has been retired to a measurement
    retired = sa.Column(sa.Boolean(), nullable=False, index=True, default=False)

    # The GSRN number this GGO was issued at (if issued=True)
    issue_gsrn = sa.Column(sa.String(), sa.ForeignKey('meteringpoint.gsrn'), index=True)
    issue_meteringpoint = relationship('MeteringPoint', foreign_keys=[issue_gsrn], lazy='joined', uselist=False)

    # The GSRN and Measurement address this GGO is retired to (if retired=True)
    retire_gsrn = sa.Column(sa.String(), sa.ForeignKey('meteringpoint.gsrn'), index=True)
    retire_meteringpoint = relationship('MeteringPoint', foreign_keys=[retire_gsrn], lazy='joined', uselist=False)

    retire_measurement_id = sa.Column(sa.Integer(), sa.ForeignKey('measurement.id'))
    retire_measurement = relationship('Measurement', foreign_keys=[retire_measurement_id])

    # Emissions
    emissions = sa.Column(JSONB())

    def is_tradable(self):
        """
        :rtype: bool
        """
        return not self.is_expired()

    def is_expired(self):
        """
        :rtype: bool
        """
        return datetime.now(tz=timezone.utc) >= self.expire_time

    @property
    def meteringpoint(self):
        """
        Returns the MeteringPoint which this GGO was issued to.

        :rtype: datahub.meteringpoints.MeteringPoint
        """
        return self.measurement.meteringpoint if self.measurement else None

    @property
    def gsrn(self):
        """
        Returns the GSRN number of the MeteringPoint which this
        GGO was issued to.

        :rtype: str
        """
        return self.meteringpoint.gsrn if self.meteringpoint else None

    @classmethod
    def from_measurement(cls, measurement):
        """
        Create a new GGO from a measurement.

        :param origin.measurements.Measurement measurement:
        :rtype: Ggo
        """
        assert 0 < measurement.amount

        now = datetime.now(tz=timezone.utc)

        return cls(
            issue_time=now,
            expire_time=now + GGO_EXPIRE_TIME,
            begin=measurement.begin,
            end=measurement.end,
            amount=measurement.amount,
            sector=measurement.meteringpoint.sector,
            user=measurement.meteringpoint.user,
            measurement=measurement,
            subject=measurement.meteringpoint.subject,
            tech_code=measurement.meteringpoint.tech_code,
            fuel_code=measurement.meteringpoint.fuel_code,
            issued=True,
            stored=True,
            retired=False,
        )

    def create_child(self, amount, user):
        """
        Creates a new child Ggo.

        :param int amount:
        :param User user:
        :rtype: Ggo
        """
        assert 0 < amount <= self.amount

        return Ggo(
            subject=user.subject,
            parent_id=self.id,
            issue_time=self.issue_time,
            expire_time=self.expire_time,
            sector=self.sector,
            begin=self.begin,
            end=self.end,
            tech_code=self.tech_code,
            fuel_code=self.fuel_code,
            emissions=self.emissions,
            amount=amount,
            issued=False,
            stored=False,
            retired=False,
        )


@sa.event.listens_for(Ggo, 'before_insert')
def on_before_creating_task(mapper, connect, ggo):
    if not ggo.public_id:
        ggo.public_id = str(uuid4())


# -- Ledger ------------------------------------------------------------------


class BatchState(Enum):
    """
    States in which a Batch can exist
    """
    # Step 1: The batch has been submitted to the database
    PENDING = 'PENDING'
    # Step 2: The batch has been submitted to the ledger
    SUBMITTED = 'SUBMITTED'
    # Step 3/1: The batch failed to be processed on the ledger
    DECLINED = 'DECLINED'
    # Step 3/2: The batch was processes successfully on the ledger
    COMPLETED = 'COMPLETED'


class Batch(ModelBase):
    """
    Represents a batch of transactions, which can be executed on the ledger
    atomically. Use build_ledger_batch() to build a Batch object from the
    origin_ledger_sdk library.

    Transactions are executed in the order that are added using
    add_transaction().

    Invoke lifecycle hooks to synchronize the database with the batch status:

        - Invoke on_begin() immediately after creating the batch, before
          inserting it into the database

        - Invoke on_submitted() once the batch has been submitted to the ledger

        - Invoke on_commit() once/if the batch has been completed on the ledger

        - Invoke on_rollback() once/if the batch has been declined on the ledger

    """
    __tablename__ = 'ledger_batch'

    id = sa.Column(sa.Integer(), primary_key=True, index=True)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    state: BatchState = sa.Column(sa.Enum(BatchState), nullable=False)

    # Time when batch was LAST submitted to ledger (if at all)
    submitted = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    user_subject = sa.Column(sa.String(), sa.ForeignKey('user.subject'), index=True, nullable=False)
    user = relationship('User', foreign_keys=[user_subject])
    transactions = relationship('Transaction', back_populates='batch', uselist=True, order_by='asc(Transaction.order)')

    # The handle returned by the ledger used to enquiry for status
    handle = sa.Column(sa.String())

    # How many times the ledger has been polled, asking for batch status
    poll_count = sa.Column(sa.Integer(), nullable=False, default=0)

    def add_transaction(self, transaction):
        """
        :param Transaction transaction:
        """
        transaction.order = len(self.transactions)
        self.transactions.append(transaction)

    def add_all_transactions(self, transactions):
        """
        :param collections.abc.Iterable[Transaction] transactions:
        """
        for transaction in transactions:
            self.add_transaction(transaction)

    def on_begin(self):
        self.state = BatchState.PENDING

        for transaction in self.transactions:
            transaction.on_begin()

    def on_submitted(self, handle):
        """
        :param str handle:
        """
        self.state = BatchState.SUBMITTED
        self.handle = handle
        self.submitted = func.now()

    def on_commit(self):
        self.state = BatchState.COMPLETED

        for transaction in self.transactions:
            transaction.on_commit()

    def on_rollback(self):
        self.state = BatchState.DECLINED

        session = Session.object_session(self)

        for transaction in reversed(self.transactions):
            transaction.on_rollback()
            session.delete(transaction)


class Transaction(ModelBase):
    """
    Abstract base class for ledger transactions. Available transactions
    are implemented below this class.
    """
    __abstract__ = False
    __tablename__ = 'ledger_transaction'
    __table_args__ = (
        sa.UniqueConstraint('parent_ggo_id'),
        sa.UniqueConstraint('batch_id', 'order'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, index=True)
    order = sa.Column(sa.Integer(), nullable=False)

    # Polymorphism
    type = sa.Column(sa.String(20), nullable=False)
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'transaction',
    }

    @declared_attr
    def batch_id(cls):
        return sa.Column(sa.Integer(), sa.ForeignKey('ledger_batch.id'), index=True, nullable=False)

    @declared_attr
    def batch(cls):
        return relationship('Batch', foreign_keys=[cls.batch_id], back_populates='transactions')

    @declared_attr
    def parent_ggo_id(cls):
        return sa.Column(sa.Integer(), sa.ForeignKey('ggo.id'), index=True, nullable=False)

    @declared_attr
    def parent_ggo(cls):
        return relationship('Ggo', foreign_keys=[cls.parent_ggo_id])

    def on_begin(self):
        raise NotImplementedError

    def on_commit(self):
        raise NotImplementedError

    def on_rollback(self):
        raise NotImplementedError

    def build_ledger_request(self):
        raise NotImplementedError


class SplitTransaction(Transaction):
    """
    Splits parent_ggo into multiple new GGOs. The sum of the target GGOs
    must be equal to the parent_ggo's amount.
    """
    __abstract__ = False
    __tablename__ = 'ledger_transaction'
    __mapper_args__ = {'polymorphic_identity': 'split'}
    __table_args__ = (
        {'extend_existing': True},
    )

    # The target GGOs (children)
    targets = relationship('SplitTarget', back_populates='transaction', uselist=True)

    def add_target(self, ggo, reference=None):
        """
        :param Ggo ggo:
        :param str reference:
        """
        self.targets.append(SplitTarget(
            transaction=self,
            reference=reference,
            ggo=ggo,
        ))

    def on_begin(self):
        assert sum(t.ggo.amount for t in self.targets) == self.parent_ggo.amount
        assert self.parent_ggo.stored is True
        assert self.parent_ggo.retired is False

        self.parent_ggo.stored = False

        for target in self.targets:
            target.ggo.stored = True

    def on_commit(self):
        self.parent_ggo.stored = False

        for target in self.targets:
            target.ggo.stored = True

    def on_rollback(self):
        self.parent_ggo.stored = True

        session = Session.object_session(self)

        for target in self.targets:
            session.delete(target)
            session.delete(target.ggo)


class SplitTarget(ModelBase):
    """
    A target GGO when splitting a GGO into multiple GGOs.
    Is used in conjunction with SplitTransaction.

    "reference" is an arbitrary string provided by the user, which can be
    used for future enquiry into transferring statistics.
    """
    __tablename__ = 'ledger_split_target'
    __table_args__ = (
        sa.UniqueConstraint('ggo_id'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, index=True)

    transaction_id = sa.Column(sa.Integer(), sa.ForeignKey('ledger_transaction.id'), index=True)
    transaction = relationship('SplitTransaction', foreign_keys=[transaction_id])

    ggo_id = sa.Column(sa.Integer(), sa.ForeignKey('ggo.id'), index=True)
    ggo = relationship('Ggo', foreign_keys=[ggo_id])

    # Client reference, like Agreement ID etc.
    reference = sa.Column(sa.String(), index=True)


class RetireTransaction(Transaction):
    """
    Retires parent_ggo to the provided measurement of the provided
    meteringpoint. The sum of the target GGOs must be equal to the
    parent_ggo's amount.
    """
    __abstract__ = False
    __tablename__ = 'ledger_transaction'
    __mapper_args__ = {'polymorphic_identity': 'retire'}
    __table_args__ = (
        {'extend_existing': True},
    )

    # The begin of the measurement
    begin = sa.Column(sa.DateTime(timezone=True))

    # The meteringpoint which the measurement were published to
    meteringpoint_id = sa.Column(sa.Integer(), sa.ForeignKey('meteringpoint.id'))
    meteringpoint = relationship('MeteringPoint', foreign_keys=[meteringpoint_id])

    # Measurement to retire GGO to
    measurement_id = sa.Column(sa.Integer(), sa.ForeignKey('measurement.id'))
    measurement = relationship('Measurement', foreign_keys=[measurement_id])
    # measurement_address = sa.Column(sa.String())

    @staticmethod
    def build(ggo, meteringpoint, measurement_id):
        """
        Retires the provided GGO to the measurement at the provided address.
        The provided meteringpoint

        :param Ggo ggo:
        :param MeteringPoint meteringpoint:
        :param int measurement_id:
        :rtype: RetireTransaction
        """
        ggo.retire_gsrn = meteringpoint.gsrn
        ggo.retire_measurement_id = measurement_id

        return RetireTransaction(
            parent_ggo=ggo,
            begin=ggo.begin,
            meteringpoint=meteringpoint,
            measurement_id=measurement_id,
        )

    def on_begin(self):
        self.parent_ggo.stored = False
        self.parent_ggo.retired = True

    def on_commit(self):
        self.parent_ggo.stored = False
        self.parent_ggo.retired = True

    def on_rollback(self):
        self.parent_ggo.stored = True  # TODO test this
        self.parent_ggo.retired = False
        self.parent_ggo.retire_gsrn = None  # TODO test this
        self.parent_ggo.measurement_id = None  # TODO test this
