from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Account:
    id: str


@dataclass
class MappedUser:
    """
    Replicates the data structure of a User,
    but is compatible with marshmallow_dataclass obj-to-JSON
    """
    subject: str = field(metadata=dict(data_key='id'))
    name: str
    company: str
    email: str
    has_performed_onboarding: bool = True
    accounts: List[Account] = field(default_factory=list)
    phone: Optional[str] = field(default=None)


@dataclass
class GetOnboardingUrlRequest:
    return_url: str = field(metadata=dict(data_key='returnUrl'))


@dataclass
class GetOnboardingUrlResponse:
    success: bool
    url: str


@dataclass
class OnboardingCallbackRequest:
    sub: str


# -- Signup request and response ---------------------------------------------


@dataclass
class SignupRequest:
    email: str
    phone: str
    password: str
    name: str
    company: str


@dataclass
class SignupResponse:
    success: bool
    token: Optional[str]
    user: Optional[MappedUser]


# -- Login request and response ----------------------------------------------


@dataclass
class LoginRequest:
    email: str
    password: str


@dataclass
class LoginResponse:
    success: bool
    token: Optional[str]
    user: Optional[MappedUser]


# -- GetProfile request and response -----------------------------------------


@dataclass
class GetProfileResponse:
    success: bool
    user: MappedUser


# -- SearchUsers request and response ----------------------------------------


@dataclass
class AutocompleteUsersRequest:
    query: str


@dataclass
class AutocompleteUsersResponse:
    success: bool
    users: List[MappedUser]
