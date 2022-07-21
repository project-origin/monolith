from .agreements import TradeAgreement, AgreementState, AgreementDirection
from .auth import User
from .ggo import Ggo, Batch, Transaction, SplitTransaction, SplitTarget, RetireTransaction
from .measurements import Measurement
from .meteringpoints import MeteringPoint, MeteringPointTag
from .technologies import Technology

# This is a list of all database models to include when creating
# database migrations.

VERSIONED_DB_MODELS = (
    TradeAgreement,
    AgreementState,
    AgreementDirection,
    User,
    Ggo,
    Batch,
    Transaction,
    SplitTransaction,
    SplitTarget,
    RetireTransaction,
    Measurement,
    MeteringPoint,
    MeteringPointTag,
    Technology,
)
