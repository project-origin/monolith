from dataclasses import dataclass, field
from typing import List


@dataclass
class MappedTechnology:
    technology: str
    tech_code: str = field(metadata=dict(data_key='technologyCode'))
    fuel_code: str = field(metadata=dict(data_key='fuelCode'))


# -- GetTechnologies request and response ------------------------------------


@dataclass
class GetTechnologiesResponse:
    success: bool
    technologies: List[MappedTechnology] = field(default_factory=list)
