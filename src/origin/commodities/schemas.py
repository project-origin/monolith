from typing import List
from dataclasses import dataclass, field

from origin.common import DateRange, DataSet
from origin.facilities import FacilityFilters
from origin.ggo.schemas import GgoCategory
from origin.measurements import MappedMeasurement
from origin.meteringpoints import MeteringPointType


@dataclass
class GgoTechnology:
    technology: str
    amount: int
    unit: str = 'Wh'


@dataclass
class GgoDistribution:
    technologies: List[GgoTechnology] = field(default_factory=list)

    @property
    def total(self):
        return sum(t.amount for t in self.technologies)

    @property
    def unit(self):
        return 'Wh'


@dataclass
class GgoDistributionBundle:
    issued: GgoDistribution = field(default_factory=GgoDistribution)
    stored: GgoDistribution = field(default_factory=GgoDistribution)
    retired: GgoDistribution = field(default_factory=GgoDistribution)
    expired: GgoDistribution = field(default_factory=GgoDistribution)
    inbound: GgoDistribution = field(default_factory=GgoDistribution)
    outbound: GgoDistribution = field(default_factory=GgoDistribution)


# -- GetGgoDistributions request and response --------------------------------


@dataclass
class GetGgoDistributionsRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))


@dataclass
class GetGgoDistributionsResponse:
    success: bool
    distributions: GgoDistributionBundle


# -- GetGgoSummary request and response --------------------------------------


@dataclass
class GetGgoSummaryRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    category: GgoCategory = field(metadata=dict(by_value=True))
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))


@dataclass
class GetGgoSummaryResponse:
    success: bool
    labels: List[str] = field(default_factory=list)
    ggos: List[DataSet] = field(default_factory=list)


# -- GetMeasurements request and response ------------------------------------


@dataclass
class GetMeasurementsRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))
    filters: FacilityFilters = field(default=None)
    measurement_type: MeteringPointType = field(default=None, metadata=dict(data_key='measurementType', by_value=True))


@dataclass
class GetMeasurementsResponse:
    success: bool
    labels: List[str] = field(default_factory=list)
    measurements: DataSet = field(default=None)


# -- GetPeakMeasurement request and response ---------------------------------


@dataclass
class GetPeakMeasurementRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))
    measurement_type: MeteringPointType = field(default=None, metadata=dict(data_key='measurementType', by_value=True))


@dataclass
class GetPeakMeasurementResponse:
    success: bool
    measurement: MappedMeasurement = None
