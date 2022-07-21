import marshmallow
from enum import Enum
from typing import List, Union
from marshmallow_dataclass import NewType
from dataclasses import dataclass, field

from origin.config import UNKNOWN_TECHNOLOGY_LABEL
from origin.meteringpoints import MeteringPointFilters, MeteringPointType


class FacilityOrder(Enum):
    NAME = 'name'
    RETIRE_PRIORITY = 'retirePriority'


# -- Common ------------------------------------------------------------------


FacilityTechnology = NewType(
    name='FacilityTechnology',
    typ=str,
    field=marshmallow.fields.Function,
    serialize=lambda facility: (facility.technology.technology
                                if facility.technology
                                else UNKNOWN_TECHNOLOGY_LABEL),
)


FacilityTagList = NewType(
    name='FacilityTag',
    typ=str,
    field=marshmallow.fields.Function,
    serialize=lambda facility: [t.tag for t in facility.tags],
)


@dataclass
class MappedFacility:
    """
    Replicates the data structure of a Facility, but is compatible
    with marshmallow_dataclass obj-to-JSON
    """
    public_id: str = field(metadata=dict(data_key='id'))
    retiring_priority: int = field(metadata=dict(data_key='retiringPriority'))
    gsrn: str
    type: MeteringPointType = field(metadata=dict(data_key='facilityType', by_value=True))
    technology: FacilityTechnology
    technology_code: str = field(metadata=dict(data_key='technologyCode'))
    fuel_code: str = field(metadata=dict(data_key='fuelCode'))
    sector: str
    name: str
    description: str
    address: str
    city_name: str = field(metadata=dict(data_key='cityName'))
    postcode: str
    municipality_code: str = field(metadata=dict(data_key='municipalityCode'))
    tags: FacilityTagList = field(default_factory=list)


@dataclass
class FacilityFilters(MeteringPointFilters):
    """
    Inherits from MeteringPointFilters, but with modifications.
    """
    type: Union[MeteringPointType, str] = field(default=None, metadata=dict(by_value=True, data_key='facilityType'))


# -- GetFacilityList request and response ------------------------------------


@dataclass
class GetFacilityListRequest:
    filters: FacilityFilters = None
    order_by: FacilityOrder = field(default=None, metadata=dict(data_key='orderBy', by_value=True))


@dataclass
class GetFacilityListResponse:
    success: bool
    facilities: List[MappedFacility] = field(default_factory=list)


# -- GetFilteringOptions request and response --------------------------------


@dataclass
class GetFilteringOptionsRequest:
    filters: FacilityFilters = None


@dataclass
class GetFilteringOptionsResponse:
    success: bool
    sectors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)


# -- EditFacilityDetails request and response --------------------------------


@dataclass
class EditFacilityDetailsRequest:
    id: str
    name: str
    tags: List[str] = field(default_factory=list)


@dataclass
class EditFacilityDetailsResponse:
    success: bool


# -- SetRetiringPriority request and response --------------------------------


@dataclass
class SetRetiringPriorityRequest:
    public_ids_prioritized: List[str] = field(default_factory=list, metadata=dict(data_key='idsPrioritized', missing=[]))


@dataclass
class SetRetiringPriorityResponse:
    success: bool
