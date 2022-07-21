from marshmallow import validate, EXCLUDE
from typing import List
from dataclasses import dataclass, field

from origin.meteringpoints import MappedMeteringPoint
from origin.auth import subject_exists
from origin.common import Unit, DateRange, DataSet

from .models import AgreementState, AgreementDirection


# ----------------------------------------------------------------------------


@dataclass
class MappedTradeAgreement:
    state: AgreementState = field(metadata=dict(by_value=True))
    direction: AgreementDirection = field(metadata=dict(by_value=True))
    counterpart_subject: str = field(metadata=dict(data_key='counterpartId'))
    counterpart: str
    public_id: str = field(metadata=dict(data_key='id'))
    date_from: str = field(metadata=dict(data_key='dateFrom'))
    date_to: str = field(metadata=dict(data_key='dateTo'))
    amount: int
    amount_percent: int = field(metadata=dict(data_key='amountPercent'))
    unit: Unit
    technologies: List[str]
    reference: str
    limit_to_consumption: bool = field(metadata=dict(data_key='limitToConsumption'))
    proposal_note: str = field(metadata=dict(data_key='proposalNote', allow_none=True))

    # Only for the outbound-user of an agreement
    facilities: List[MappedMeteringPoint] = field(default_factory=list)


# -- GetAgreementList request and response -----------------------------------


@dataclass
class GetAgreementListResponse:
    success: bool
    pending: List[MappedTradeAgreement] = field(default_factory=list)
    sent: List[MappedTradeAgreement] = field(default_factory=list)
    inbound: List[MappedTradeAgreement] = field(default_factory=list)
    outbound: List[MappedTradeAgreement] = field(default_factory=list)
    cancelled: List[MappedTradeAgreement] = field(default_factory=list)
    declined: List[MappedTradeAgreement] = field(default_factory=list)


# -- GetAgreementSummary request and response --------------------------------


@dataclass
class GetAgreementDetailsRequest:
    public_id: str = field(default=None, metadata=dict(data_key='id'))


@dataclass
class GetAgreementDetailsResponse:
    success: bool
    agreement: MappedTradeAgreement = field(default=None)


# -- GetAgreementSummary request and response --------------------------------


@dataclass
class GetAgreementSummaryRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    date_range: DateRange = field(default=None, metadata=dict(data_key='dateRange'))
    public_id: str = field(default=None, metadata=dict(data_key='id'))
    direction: AgreementDirection = field(default=None, metadata=dict(by_value=True))


@dataclass
class GetAgreementSummaryResponse:
    success: bool
    labels: List[str]
    ggos: List[DataSet]


# -- CancelAgreement request and response ------------------------------------


@dataclass
class CancelAgreementRequest:
    public_id: str = field(metadata=dict(data_key='id'))


# -- SetTransferPriority request and response ------------------------------------


@dataclass
class SetTransferPriorityRequest:
    public_ids_prioritized: List[str] = field(default_factory=list, metadata=dict(data_key='idsPrioritized', missing=[]))


# -- SetFacilities request and response ------------------------------------


@dataclass
class SetFacilitiesRequest:
    public_id: str = field(metadata=dict(data_key='id'))
    facility_public_ids: List[str] = field(default_factory=list, metadata=dict(data_key='facilityIds', missing=[]))


# -- FindSuppliers request and response --------------------------------------


@dataclass
class GgoSupplier:
    sub: str = field(metadata=dict(data_key='id'))
    company: str


@dataclass
class FindSuppliersRequest:
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))
    min_amount: int = field(metadata=dict(data_key='minAmount'))


@dataclass
class FindSuppliersResponse:
    success: bool
    suppliers: List[GgoSupplier]


# -- SubmitAgreementProposal request and response ----------------------------


@dataclass
class SubmitAgreementProposalRequest:
    direction: AgreementDirection = field(metadata=dict(by_value=True))
    reference: str = field(metadata=dict(validate=validate.Length(min=1)))
    counterpart_subject: str = field(metadata=dict(data_key='counterpartId', validate=(validate.Length(min=1), subject_exists)))
    amount: int
    unit: Unit
    amount_percent: int = field(metadata=dict(allow_none=True, data_key='amountPercent', validate=validate.Range(min=1, max=100)))
    date: DateRange
    limit_to_consumption: bool = field(metadata=dict(data_key='limitToConsumption'))
    proposal_note: str = field(metadata=dict(data_key='proposalNote', allow_none=True))
    technologies: List[str] = field(default_factory=None)
    facility_gsrn: List[str] = field(default_factory=list, metadata=dict(data_key='facilityGsrn'))

    class Meta:
        unknown = EXCLUDE


@dataclass
class SubmitAgreementProposalResponse:
    success: bool


# -- RespondToProposal request and response ----------------------------------


@dataclass
class RespondToProposalRequest:
    public_id: str = field(metadata=dict(data_key='id'))
    accept: bool
    technologies: List[str] = field(default_factory=None)
    facility_gsrn: List[str] = field(default_factory=list, metadata=dict(data_key='facilityGsrn'))
    amount_percent: int = field(default_factory=list, metadata=dict(allow_none=True, data_key='amountPercent'))


# -- WithdrawProposal request and response -----------------------------------


@dataclass
class WithdrawProposalRequest:
    public_id: str = field(metadata=dict(data_key='id'))


# -- CountPendingProposals request and response ------------------------------


@dataclass
class CountPendingProposalsResponse:
    success: bool
    count: int
