import marshmallow_dataclass as md

from origin.http import Controller
from origin.auth import User, requires_login
from origin.db import inject_session, atomic
from origin.technologies import Technology
from origin.meteringpoints import \
    MeteringPoint, MeteringPointTag, MeteringPointQuery

from .schemas import (
    FacilityOrder,
    GetFacilityListRequest,
    GetFacilityListResponse,
    EditFacilityDetailsRequest,
    EditFacilityDetailsResponse,
    GetFilteringOptionsRequest,
    GetFilteringOptionsResponse,
    SetRetiringPriorityRequest,
    SetRetiringPriorityResponse,
)


class GetFacilityList(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetFacilityListRequest)
    Response = md.class_schema(GetFacilityListResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetFacilityListRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetFacilityListResponse
        """
        query = MeteringPointQuery(session) \
            .belongs_to(user)

        # Filters
        if request.filters:
            query = query.apply_filters(request.filters)

        # Order by
        if request.order_by is FacilityOrder.NAME:
            query = query.order_by(MeteringPoint.name.asc())
        elif request.order_by is FacilityOrder.RETIRE_PRIORITY:
            query = query.order_by(MeteringPoint.retiring_priority.asc())

        return GetFacilityListResponse(
            success=True,
            facilities=query.all(),
        )


class EditFacilityDetails(Controller):
    """
    TODO
    """
    Request = md.class_schema(EditFacilityDetailsRequest)
    Response = md.class_schema(EditFacilityDetailsResponse)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param EditFacilityDetailsRequest request:
        :param User user:
        :param Session session:
        :rtype: EditFacilityDetailsResponse
        """
        meteringpoint = MeteringPointQuery(session) \
            .belongs_to(user) \
            .has_public_id(request.id) \
            .one_or_none()

        if not meteringpoint:
            return EditFacilityDetailsResponse(success=False)

        # TODO do this in a more clean way
        meteringpoint.name = request.name
        meteringpoint.tags = []
        session.flush()
        meteringpoint.tags = [MeteringPointTag(tag=t) for t in request.tags]

        return GetFilteringOptionsResponse(success=True)


class GetFilteringOptions(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetFilteringOptionsRequest)
    Response = md.class_schema(GetFilteringOptionsResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetFilteringOptionsRequest request:
        :param User user:
        :param Session session:
        :rtype: GetFilteringOptionsResponse
        """
        facilities = MeteringPointQuery(session) \
            .belongs_to(user)

        # Filters
        if request.filters:
            facilities = facilities.apply_filters(request.filters)

        return GetFilteringOptionsResponse(
            success=True,
            sectors=facilities.get_distinct_sectors(),
            tags=facilities.get_distinct_tags(),
            technologies=self.get_technologies(session),
        )

    def get_technologies(self, session):
        """
        rtype: list[str]
        """
        query = session.query(Technology.technology.distinct())
        return [row[0] for row in query.all()]


class SetRetiringPriority(Controller):
    """
    TODO
    """
    Request = md.class_schema(SetRetiringPriorityRequest)
    Response = md.class_schema(SetRetiringPriorityResponse)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param SetRetiringPriorityRequest request:
        :param User user:
        :param Session session:
        :rtype: GetFilteringOptionsResponse
        """
        facilities = MeteringPointQuery(session) \
            .belongs_to(user) \
            .is_consumer()

        # Initially remove priority for all facilities
        facilities.update({MeteringPoint.retiring_priority: None})

        # Set priorities in the order they were provided
        for i, public_id in enumerate(request.public_ids_prioritized):
            facilities \
                .has_public_id(public_id) \
                .update({MeteringPoint.retiring_priority: i})

        return GetFilteringOptionsResponse(success=True)


# class RetireBackInTime(Controller):
#     """
#     Starts a pipeline to retire GGOs back in time.
#     """
#     datahub = DataHubService()
#
#     @requires_login
#     @inject_session
#     def handle_request(self, user, session):
#         """
#         :param User user:
#         :param Session session:
#         :rtype: bool
#         """
#         gsrn = FacilityQuery(session) \
#             .belongs_to(user) \
#             .is_consumer() \
#             .get_distinct_gsrn()
#
#         if gsrn:
#             # Get first and last "begin" for all measurements of all
#             # facilities which are retiring GGOs
#             response = self.datahub.get_measurement_begin_range(
#                 token=user.access_token,
#                 request=GetBeginRangeRequest(
#                     filters=MeasurementFilters(gsrn=gsrn),
#                 )
#             )
#
#             if response.first and response.last:
#                 start_consume_back_in_time_pipeline(
#                     user=user,
#                     begin_from=response.first,
#                     begin_to=response.last,
#                 )
#
#         return True
