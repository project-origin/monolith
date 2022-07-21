import marshmallow_dataclass as md

from origin.http import Controller
from origin.db import inject_session, atomic
from origin.auth import requires_login
from .hashing import password_hash

from .models import User
from .queries import UserQuery
from .tokens import token_encoder
from .schemas import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    MappedUser,
    GetProfileResponse,
    Account,
    AutocompleteUsersRequest,
    AutocompleteUsersResponse,
)


class Signup(Controller):
    """
    Refreshes user's profile data along with tokens,
    and returns the User profile.
    """
    Request = md.class_schema(SignupRequest)
    Response = md.class_schema(SignupResponse)

    def handle_request(self, request):
        """
        :param SignupRequest request:
        :rtype: GetProfileResponse
        """
        user = self.create_user(request)
        token = token_encoder.encode(user.subject)

        return LoginResponse(
            success=True,
            token=token,
            user=user,
        )

    @atomic
    def create_user(self, request, session):
        """
        :param SignupRequest request:
        :param sqlalchemy.orm.Session session:
        :rtype: User
        """
        user = User(
            email=request.email,
            phone=request.phone,
            password=password_hash(request.password),
            name=request.name,
            company=request.company,
        )

        session.add(user)

        return user


class Login(Controller):
    """
    Refreshes user's profile data along with tokens,
    and returns the User profile.
    """
    Request = md.class_schema(LoginRequest)
    Response = md.class_schema(LoginResponse)

    @inject_session
    def handle_request(self, request, session):
        """
        :param LoginRequest request:
        :param sqlalchemy.orm.Session session:
        :rtype: GetProfileResponse
        """
        user = UserQuery(session) \
            .has_email(request.email) \
            .has_password(request.password) \
            .one_or_none()

        if user is not None:
            success = True
            token = token_encoder.encode(user.subject)
        else:
            success = False
            token = None

        return LoginResponse(
            success=success,
            token=token,
            user=user,
        )


class GetProfile(Controller):
    """
    Refreshes user's profile data along with tokens,
    and returns the User profile.
    """
    Response = md.class_schema(GetProfileResponse)

    @requires_login
    @inject_session
    def handle_request(self, user, session):
        """
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetProfileResponse
        """
        return GetProfileResponse(
            success=True,
            user=MappedUser(
                subject=user.subject,
                name=user.name,
                company=user.company,
                email=user.email,
                phone=user.phone,
                has_performed_onboarding=False,
                accounts=[Account(id=user.subject)],
            ),
        )


class AutocompleteUsers(Controller):
    """
    TODO
    """
    Request = md.class_schema(AutocompleteUsersRequest)
    Response = md.class_schema(AutocompleteUsersResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param AutocompleteUsersRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: AutocompleteUsersResponse
        """
        users = UserQuery(session) \
            .is_active() \
            .starts_with(request.query) \
            .exclude(user) \
            .order_by(User.name.asc()) \
            .all()

        return AutocompleteUsersResponse(
            success=True,
            users=users,
        )
