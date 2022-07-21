import marshmallow_dataclass as md

from origin.http import Controller
from origin.db import inject_session
from origin.auth import requires_login

from .queries import MeasurementQuery
from .models import Measurement, MeteringPointType
from .schemas import (
    GetMeasurementResponse,
    GetMeasurementRequest,
    GetMeasurementListRequest,
    GetMeasurementListResponse,
    GetBeginRangeRequest,
    GetBeginRangeResponse,
    GetMeasurementSummaryRequest,
    GetMeasurementSummaryResponse,
)


# class GetMeasurement(Controller):
#     """
#     Returns a single Measurement object of a specific type,
#     either PRODUCTION or CONSUMPTION.
#     """
#     Request = md.class_schema(GetMeasurementRequest)
#     Response = md.class_schema(GetMeasurementResponse)
#
#     def __init__(self, measurement_type):
#         """
#         :param MeteringPointType measurement_type:
#         """
#         self.measurement_type = measurement_type
#
#     @requires_login
#     @inject_session
#     def handle_request(self, request, user, session):
#         """
#         :param GetMeasurementRequest request:
#         :param origin.auth.User user:
#         :param sqlalchemy.orm.Session session:
#         :rtype: GetMeasurementResponse
#         """
#         measurement = MeasurementQuery(session) \
#             .belongs_to(user) \
#             .is_type(self.measurement_type) \
#             .has_gsrn(request.gsrn) \
#             .begins_at(request.begin) \
#             .one_or_none()
#
#         return GetMeasurementResponse(
#             success=measurement is not None,
#             measurement=measurement,
#         )


class GetMeasurementList(Controller):
    """
    Returns a list of Measurement objects which belongs to any of the
    user's MeteringPoints with options to filter/narrow down the results.
    Can only select MeteringPoints which belongs to the user.
    """
    Request = md.class_schema(GetMeasurementListRequest)
    Response = md.class_schema(GetMeasurementListResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetMeasurementListRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetMeasurementListResponse
        """
        query = MeasurementQuery(session) \
            .belongs_to(user)

        if request.filters:
            query = query.apply_filters(request.filters)

        results = query \
            .order_by(self.get_order_by(request)) \
            .offset(request.offset)

        if request.limit:
            results = results.limit(request.limit)

        return GetMeasurementListResponse(
            success=True,
            total=query.count(),
            measurements=results.all(),
        )

    def get_order_by(self, request):
        """
        :param GetMeasurementListRequest request:
        """
        if request.order == 'begin':
            field = Measurement.begin
        elif request.order == 'amount':
            field = Measurement.amount
        else:
            raise RuntimeError('Should NOT have happened')

        if request.sort == 'asc':
            return field.asc()
        elif request.sort == 'desc':
            return field.desc()
        else:
            raise RuntimeError('Should NOT have happened')


class GetBeginRange(Controller):
    """
    Given a set of filters, this endpoint returns the first and
    last "begin" for all measurements in the result set.
    Useful for checking when measuring began and ended.
    """
    Request = md.class_schema(GetBeginRangeRequest)
    Response = md.class_schema(GetBeginRangeResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetBeginRangeRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetBeginRangeResponse
        """
        query = MeasurementQuery(session) \
            .belongs_to(user)

        if request.filters:
            query = query.apply_filters(request.filters)

        return GetBeginRangeResponse(
            success=True,
            first=query.get_first_measured_begin(),
            last=query.get_last_measured_begin(),
        )


class GetMeasurementSummary(Controller):
    """
    Returns a summary of the user's Measurements, or a subset hereof.
    Useful for plotting or visualizing data, or wherever aggregated
    data is needed.
    """
    Request = md.class_schema(GetMeasurementSummaryRequest)
    Response = md.class_schema(GetMeasurementSummaryResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetMeasurementSummaryRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetMeasurementSummaryResponse
        """
        query = MeasurementQuery(session) \
            .belongs_to(user)

        if request.filters:
            query = query.apply_filters(request.filters)

        summary = query.get_summary(
            request.resolution, request.grouping, request.utc_offset)

        if request.fill and request.filters.begin_range:
            summary.fill(request.filters.begin_range)

        return GetMeasurementSummaryResponse(
            success=True,
            labels=summary.labels,
            groups=summary.groups,
        )
