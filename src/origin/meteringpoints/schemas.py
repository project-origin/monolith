import marshmallow
from typing import List, Optional
from dataclasses import dataclass, field
from marshmallow_dataclass import NewType

from origin.config import UNKNOWN_TECHNOLOGY_LABEL

from .models import MeteringPointType


MeteringPointTechnology = NewType(
    name='MeteringPointTechnology',
    typ=str,
    field=marshmallow.fields.Function,
    serialize=lambda meteringpoint: (meteringpoint.technology.technology
                                     if meteringpoint.technology
                                     else UNKNOWN_TECHNOLOGY_LABEL),
)


FacilityTagList = NewType(
    name='FacilityTag',
    typ=str,
    field=marshmallow.fields.Function,
    serialize=lambda facility: [t.tag for t in facility.tags],
)


@dataclass
class MappedMeteringPoint:
    """
    A reflection of the MappedMetering class above, but supports JSON schema
    serialization/deserialization using marshmallow/marshmallow-dataclass.
    """
    public_id: str = field(metadata=dict(data_key='id'))
    retiring_priority: int = field(metadata=dict(data_key='retiringPriority'))
    gsrn: str
    type: MeteringPointType = field(metadata=dict(by_value=True))
    technology: MeteringPointTechnology
    tech_code: str = field(metadata=dict(data_key='technologyCode'))
    fuel_code: str = field(metadata=dict(data_key='fuelCode'))

    sector: str
    name: str
    description: str

    address: str
    city_name: str = field(metadata=dict(data_key='cityName'))
    postcode: str = field(metadata=dict(data_key='postCode'))
    municipality_code: str = field(metadata=dict(data_key='municipalityCode'))
    tags: FacilityTagList = field(default_factory=list)


@dataclass
class MeteringPointFilters:
    type: str = field(default=None, metadata=dict(data_key='type'))
    gsrn: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    technology: str = field(default=None)
    text: str = field(default=None)


# @dataclass
# class MappedFacility:
#     """
#     Replicates the data structure of a Facility, but is compatible
#     with marshmallow_dataclass obj-to-JSON
#     """
#     public_id: str = field(metadata=dict(data_key='id'))
#     retiring_priority: int = field(metadata=dict(data_key='retiringPriority'))
#     gsrn: str
#     facility_type: str = field(metadata=dict(data_key='facilityType'))
#     technology: FacilityTechnology
#     technology_code: str = field(metadata=dict(data_key='technologyCode'))
#     fuel_code: str = field(metadata=dict(data_key='fuelCode'))
#     sector: str
#     name: str
#     description: str
#     address: str
#     city_name: str = field(metadata=dict(data_key='cityName'))
#     postcode: str
#     municipality_code: str = field(metadata=dict(data_key='municipalityCode'))


# -- GetMeteringPointList request and response -------------------------------


@dataclass
class GetMeteringPointListResponse:
    success: bool
    meteringpoints: List[MappedMeteringPoint] = field(default_factory=list)


# -- GetMeteringPointDetails request and response ----------------------------


@dataclass
class GetMeteringPointDetailsRequest:
    gsrn: str


@dataclass
class GetMeteringPointDetailsResponse:
    success: bool
    meteringpoint: Optional[MappedMeteringPoint] = field(default=None)


# -- SetKey request and response ---------------------------------------------


@dataclass
class SetKeyRequest:
    gsrn: str
    key: str
