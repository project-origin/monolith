from dataclasses import dataclass, field
from marshmallow.validate import Email


@dataclass
class SubmitSupportEnquiryRequest:
    email: str = field(metadata=dict(validate=Email()))
    phone: str
    message: str

    subject_type: str = field(metadata=dict(data_key='subjectType'))
    subject: str

    # Whether or not to send a recipe (email) to the user
    recipe: bool

    # Reference link/URL
    link: str = None

    # File upload
    file_name: str = field(default=None, metadata=dict(data_key='fileName'))
    file_source: str = field(default=None, metadata=dict(data_key='fileSource'))


@dataclass
class SubmitSupportEnquiryResponse:
    success: bool
