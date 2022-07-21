from typing import List
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from marshmallow import validate, validates_schema, ValidationError, post_load

from origin.validators import unique_values
from origin.meteringpoints import MeteringPointType
from origin.common import DateTimeRange, SummaryResolution, SummaryGroup


@dataclass
class MappedMeasurement:
    """
    A reflection of the Measurement class above, but supports JSON schema
    serialization/deserialization using marshmallow/marshmallow-dataclass.
    """
    address: str
    begin: datetime
    end: datetime
    amount: int
    gsrn: str
    sector: str
    type: MeteringPointType = field(metadata=dict(by_value=True))


@dataclass
class MeasurementFilters:
    """
    Filters to filter on Measurements when using MeasurementQuery.
    """
    begin: datetime = field(default=None)
    begin_range: DateTimeRange = field(default=None, metadata=dict(data_key='beginRange'))
    sector: List[str] = field(default_factory=list)
    gsrn: List[str] = field(default_factory=list)
    type: MeteringPointType = field(default=None, metadata=dict(by_value=True))

    @validates_schema
    def validate_begin_and_begin_range_mutually_exclusive(self, data, **kwargs):
        if data.get('begin') and data.get('begin_range'):
            raise ValidationError({
                'begin': ['Field is mutually exclusive with beginRange'],
                'beginRange': ['Field is mutually exclusive with begin'],
            })


# -- GetMeasurement request and response -------------------------------------


@dataclass
class GetMeasurementRequest:
    gsrn: str
    begin: datetime


@dataclass
class GetMeasurementResponse:
    success: bool
    measurement: MappedMeasurement


# -- GetMeasurementList request and response ---------------------------------


@dataclass
class GetMeasurementListRequest:

    # Offset from UTC in hours
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))

    filters: MeasurementFilters = field(default=None)
    offset: int = field(default=0)
    limit: int = field(default=None)
    order: str = field(default='begin', metadata=dict(validate=validate.OneOf(['begin', 'amount'])))
    sort: str = field(default='asc', metadata=dict(validate=validate.OneOf(['asc', 'desc'])))

    @post_load
    def apply_time_offset(self, data, **kwargs):
        """
        Applies the request utcOffset to filters.begin and filters.begin_range
        if they don't already have a UTC offset applied to them by the client.
        """
        tzinfo = timezone(timedelta(hours=data['utc_offset']))

        if data.get('filters') is not None:
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
class GetMeasurementListResponse:
    success: bool
    total: int
    measurements: List[MappedMeasurement] = field(default_factory=list)


# -- GetBeginRange request and response --------------------------------------


@dataclass
class GetBeginRangeRequest:
    filters: MeasurementFilters = field(default=None)


@dataclass
class GetBeginRangeResponse:
    success: bool
    first: datetime
    last: datetime


# -- GetGgoSummary request and response --------------------------------------


@dataclass
class GetMeasurementSummaryRequest:
    resolution: SummaryResolution
    fill: bool

    grouping: List[str] = field(metadata=dict(validate=(
        validate.ContainsOnly(('type', 'gsrn', 'sector')),
        unique_values,
    )))

    # Offset from UTC in hours
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))

    filters: MeasurementFilters = field(default=None)

    @post_load
    def apply_time_offset(self, data, **kwargs):
        """
        Applies the request utcOffset to filters.begin and filters.begin_range
        if they don't already have a UTC offset applied to them by the client.
        """
        tzinfo = timezone(timedelta(hours=data['utc_offset']))

        if data.get('filters') is not None:
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
class GetMeasurementSummaryResponse:
    success: bool
    labels: List[str] = field(default_factory=list)
    groups: List[SummaryGroup] = field(default_factory=list)
