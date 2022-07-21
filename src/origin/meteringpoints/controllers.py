import marshmallow_dataclass as md

from origin.http import Controller
from origin.db import inject_session
from origin.auth import requires_login

from .queries import MeteringPointQuery
from .schemas import (
    GetMeteringPointListResponse,
    GetMeteringPointDetailsRequest,
    GetMeteringPointDetailsResponse,
)


class GetMeteringPointList(Controller):
    """
    Returns a list of all the user's MeteringPoints.
    """
    Response = md.class_schema(GetMeteringPointListResponse)

    @requires_login
    @inject_session
    def handle_request(self, user, session):
        """
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetMeteringPointListResponse
        """
        meteringpoints = MeteringPointQuery(session) \
            .belongs_to(user) \
            .all()

        return GetMeteringPointListResponse(
            success=True,
            meteringpoints=meteringpoints,
        )


class GetMeteringPointDetails(Controller):
    """
    Returns a list of all the user's MeteringPoints.
    """
    Request = md.class_schema(GetMeteringPointDetailsRequest)
    Response = md.class_schema(GetMeteringPointDetailsResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetMeteringPointDetailsRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetMeteringPointListResponse
        """
        meteringpoint = MeteringPointQuery(session) \
            .belongs_to(user) \
            .has_gsrn(request.gsrn) \
            .one_or_none()

        return GetMeteringPointDetailsResponse(
            success=meteringpoint is not None,
            meteringpoint=meteringpoint,
        )
