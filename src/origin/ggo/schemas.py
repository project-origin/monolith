from enum import Enum
from typing import Dict, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from marshmallow import validates_schema, ValidationError, validate, post_load

from origin.auth import subject_exists
from origin.common import DateTimeRange, SummaryResolution, SummaryGroup
from origin.technologies import MappedTechnology


# @dataclass
# class MappedGgo:
#     """
#     DATAHUB SERVICE
#     A reflection of the Ggo class above, but supports JSON schema
#     serialization/deserialization using marshmallow/marshmallow-dataclass.
#     """
#     public_id: str = field(metadata=dict(data_key='id'))
#     address: str
#     begin: datetime
#     end: datetime
#     amount: int
#     gsrn: str
#     sector: str
#     issue_time: str = field(metadata=dict(data_key='issueTime'))
#     expire_time: str = field(metadata=dict(data_key='expireTime'))
#     tech_code: str = field(metadata=dict(data_key='technologyCode'))
#     fuel_code: str = field(metadata=dict(data_key='fuelCode'))
#     emissions: Dict[str, float] = field(default=None)


@dataclass
class MappedGgo:
    """
    ACCOUNT SERVICE
    A reflection of the Ggo class above, but supports JSON schema
    serialization/deserialization using marshmallow/marshmallow-dataclass.
    """
    public_id: str = field(metadata=dict(data_key='id'))
    address: str
    sector: str
    begin: datetime
    end: datetime
    amount: int
    technology: MappedTechnology
    emissions: Dict[str, float] = field(default=None)
    issue_gsrn: str = field(default=None, metadata=dict(data_key='issueGsrn'))


class GgoCategory(Enum):
    ISSUED = 'issued'
    STORED = 'stored'
    RETIRED = 'retired'
    EXPIRED = 'expired'


@dataclass
class GgoFilters:
    begin: datetime = field(default=None)
    begin_range: DateTimeRange = field(default=None, metadata=dict(data_key='beginRange'))

    address: List[str] = field(default_factory=list)
    sector: List[str] = field(default_factory=list)
    tech_code: List[str] = field(default_factory=list, metadata=dict(data_key='technologyCode'))
    fuel_code: List[str] = field(default_factory=list, metadata=dict(data_key='fuelCode'))

    category: GgoCategory = field(default=None, metadata=dict(by_value=True))
    issue_gsrn: List[str] = field(default_factory=list, metadata=dict(data_key='issueGsrn'))
    retire_gsrn: List[str] = field(default_factory=list, metadata=dict(data_key='retireGsrn'))
    retire_address: List[str] = field(default_factory=list, metadata=dict(data_key='retireAddress'))

    @validates_schema
    def validate_begin_and_begin_range_mutually_exclusive(self, data, **kwargs):
        if data.get('begin') and data.get('begin_range'):
            raise ValidationError({
                'begin': ['Field is mutually exclusive with beginRange'],
                'beginRange': ['Field is mutually exclusive with begin'],
            })


@dataclass
class TransferFilters(GgoFilters):
    reference: List[str] = field(default_factory=list, metadata=dict(allow_none=True))

    # TODO add recipient user account?


class TransferDirection(Enum):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'


@dataclass
class TransferRequest:
    amount: int = field(metadata=dict(validate=validate.Range(min=1)))
    reference: str
    account: str = field(metadata=dict(required=True, validate=subject_exists))


@dataclass
class RetireRequest:
    amount: int = field(metadata=dict(validate=validate.Range(min=1)))
    gsrn: str


# # -- GetGgoList request and response -----------------------------------------
#
#
# @dataclass
# class GetGgoListRequest:
#     gsrn: str
#     begin_range: DateTimeRange = field(metadata=dict(data_key='beginRange'))
#
#
# @dataclass
# class GetGgoListResponse:
#     success: bool
#     ggos: List[MappedGgo] = field(default_factory=list)
#
#
# # -- GetGgoList request and response -----------------------------------------
#
#
# @dataclass
# class GetGgoListRequest:
#     filters: GgoFilters
#     offset: int = field(default=0)
#     limit: int = field(default=None)
#     order: List[str] = field(default_factory=list)
#
#
# @dataclass
# class GetGgoListResponse:
#     success: bool
#     total: int
#     results: List[MappedGgo] = field(default_factory=list)
#
#
# # -- GetGgoSummary request and response --------------------------------------
#
#
# @dataclass
# class GetGgoSummaryRequest:
#     resolution: SummaryResolution = field(metadata=dict(by_value=True))
#     filters: GgoFilters
#     fill: bool
#
#     grouping: List[str] = field(metadata=dict(validate=(
#         validate.ContainsOnly(('begin', 'sector', 'technology', 'technologyCode', 'fuelCode')),
#     )))
#
#     # Offset from UTC in hours
#     utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
#
#     @post_load
#     def apply_time_offset(self, data, **kwargs):
#         """
#         Applies the request utcOffset to filters.begin and filters.begin_range
#         if they don't already have a UTC offset applied to them by the client.
#         """
#         tzinfo = timezone(timedelta(hours=data['utc_offset']))
#
#         if data['filters'].begin and data['filters'].begin.utcoffset() is None:
#             data['filters'].begin = \
#                 data['filters'].begin.replace(tzinfo=tzinfo)
#
#         if data['filters'].begin_range:
#             if data['filters'].begin_range.begin.utcoffset() is None:
#                 data['filters'].begin_range.begin = \
#                     data['filters'].begin_range.begin.replace(tzinfo=tzinfo)
#
#             if data['filters'].begin_range.end.utcoffset() is None:
#                 data['filters'].begin_range.end = \
#                     data['filters'].begin_range.end.replace(tzinfo=tzinfo)
#
#         return data
#
#
# @dataclass
# class GetGgoSummaryResponse:
#     success: bool
#     labels: List[str] = field(default_factory=list)
#     groups: List[SummaryGroup] = field(default_factory=list)





# -- GetGgoList request and response -----------------------------------------


@dataclass
class GetGgoListRequest:
    filters: GgoFilters
    offset: int = field(default=0)
    limit: int = field(default=None)
    order: List[str] = field(default_factory=list)


@dataclass
class GetGgoListResponse:
    success: bool
    total: int
    results: List[MappedGgo] = field(default_factory=list)


# -- GetGgoSummary request and response --------------------------------------


@dataclass
class GetGgoSummaryRequest:
    resolution: SummaryResolution = field(metadata=dict(by_value=True))
    filters: GgoFilters
    fill: bool

    grouping: List[str] = field(metadata=dict(validate=(
        validate.ContainsOnly(('begin', 'sector', 'technology', 'technologyCode', 'fuelCode')),
    )))

    # Offset from UTC in hours
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))

    @post_load
    def apply_time_offset(self, data, **kwargs):
        """
        Applies the request utcOffset to filters.begin and filters.begin_range
        if they don't already have a UTC offset applied to them by the client.
        """
        tzinfo = timezone(timedelta(hours=data['utc_offset']))

        if data['filters'].begin and data['filters'].begin.utcoffset() is None:
            data['filters'].begin = \
                data['filters'].begin.replace(tzinfo=tzinfo)

        if data['filters'].begin_range:
            if data['filters'].begin_range.begin.utcoffset() is None:
                data['filters'].begin_range.begin = \
                    data['filters'].begin_range.begin.replace(tzinfo=tzinfo)

            if data['filters'].begin_range.end.utcoffset() is None:
                data['filters'].begin_range.end = \
                    data['filters'].begin_range.end.replace(tzinfo=tzinfo)

        return data


@dataclass
class GetGgoSummaryResponse:
    success: bool
    labels: List[str] = field(default_factory=list)
    groups: List[SummaryGroup] = field(default_factory=list)


# # -- GetTotalAmount request and response -------------------------------------
#
#
# @dataclass
# class GetTotalAmountRequest:
#     filters: GgoFilters
#
#
# @dataclass
# class GetTotalAmountResponse:
#     success: bool
#     amount: int


# -- GetTransferSummary request and response ---------------------------------


@dataclass
class GetTransferSummaryRequest:
    resolution: SummaryResolution = field(metadata=dict(by_value=True))
    filters: TransferFilters
    fill: bool

    grouping: List[str] = field(metadata=dict(validate=(
        validate.ContainsOnly(('begin', 'sector', 'technology', 'technologyCode', 'fuelCode')),
    )))

    # Offset from UTC in hours
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))

    direction: TransferDirection = field(default=None, metadata=dict(by_value=True))

    @post_load
    def apply_time_offset(self, data, **kwargs):
        """
        Applies the request utcOffset to filters.begin and filters.begin_range
        if they don't already have a UTC offset applied to them by the client.
        """
        tzinfo = timezone(timedelta(hours=data['utc_offset']))

        if data['filters'].begin and data['filters'].begin.utcoffset() is None:
            data['filters'].begin = \
                data['filters'].begin.replace(tzinfo=tzinfo)

        if data['filters'].begin_range:
            if data['filters'].begin_range.begin.utcoffset() is None:
                data['filters'].begin_range.begin = \
                    data['filters'].begin_range.begin.replace(tzinfo=tzinfo)

            if data['filters'].begin_range.end.utcoffset() is None:
                data['filters'].begin_range.end = \
                    data['filters'].begin_range.end.replace(tzinfo=tzinfo)

        return data


@dataclass
class GetTransferSummaryResponse(GetGgoSummaryResponse):
    pass


# -- ComposeGgo request and response -----------------------------------------


@dataclass
class ComposeGgoRequest:
    id: str
    transfers: List[TransferRequest] = field(default_factory=list)
    retires: List[RetireRequest] = field(default_factory=list)


@dataclass
class ComposeGgoResponse:
    success: bool
    message: str = field(default=None)


# -- GetTransferredAmount request and response -------------------------------


@dataclass
class GetTransferredAmountRequest:
    filters: TransferFilters
    direction: TransferDirection = field(default=None, metadata=dict(by_value=True))


@dataclass
class GetTransferredAmountResponse:
    success: bool
    amount: int


# -- GetRetiredAmount request and response -----------------------------------


@dataclass
class GetRetiredAmountRequest:
    filters: GgoFilters


@dataclass
class GetRetiredAmountResponse:
    success: bool
    amount: int
