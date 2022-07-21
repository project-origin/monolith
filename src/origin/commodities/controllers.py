import marshmallow_dataclass as md
from functools import partial

from origin.http import Controller
from origin.db import inject_session
from origin.ggo import GgoQuery, GgoCategory, TransactionQuery
from origin.common import DataSet, DateTimeRange, SummaryResolution
from origin.auth import User, requires_login
from origin.measurements import MeasurementQuery, Measurement

from .schemas import (
    GgoTechnology,
    GgoDistribution,
    GgoDistributionBundle,
    GetGgoDistributionsRequest,
    GetGgoDistributionsResponse,
    GetMeasurementsRequest,
    GetMeasurementsResponse,
    GetGgoSummaryRequest,
    GetGgoSummaryResponse, GetPeakMeasurementRequest,
    GetPeakMeasurementResponse,
)


# -- Helper functions --------------------------------------------------------
from ..ggo.schemas import TransferDirection


def get_resolution(delta):
    """
    :param timedelta delta:
    :rtype: SummaryResolution
    """
    if delta.days >= (365 * 3):
        return SummaryResolution.year
    elif delta.days >= 60:
        return SummaryResolution.month
    elif delta.days >= 3:
        return SummaryResolution.day
    else:
        return SummaryResolution.hour


# -- Controllers -------------------------------------------------------------


class GetMeasurements(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetMeasurementsRequest)
    Response = md.class_schema(GetMeasurementsResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetMeasurementsRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetMeasurementsResponse
        """
        begin_range = DateTimeRange.from_date_range(request.date_range)
        resolution = get_resolution(begin_range.delta)

        query = MeasurementQuery(session) \
            .belongs_to(user) \
            .begins_within(begin_range) \
            .is_type(request.measurement_type)

        if request.filters and request.filters.gsrn:
            query = query.has_any_gsrn(request.filters.gsrn)

        summary = query.get_summary(
            resolution=resolution,
            grouping=[],
            utc_offset=request.utc_offset,
        )

        summary.fill(begin_range)

        groups = summary.groups
        label = request.measurement_type.value.capitalize()

        return GetMeasurementsResponse(
            success=True,
            labels=summary.labels,
            measurements=DataSet(
                label=label,
                values=summary.groups[0].values if groups else [],
            ),
        )


class GetGgoDistributions(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetGgoDistributionsRequest)
    Response = md.class_schema(GetGgoDistributionsResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetGgoDistributionsRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetGgoDistributionsResponse
        """
        begin_range = DateTimeRange.from_date_range(request.date_range)

        kwargs = {
            'user': user,
            'session': session,
            'begin_range': begin_range,
            'utc_offset': request.utc_offset,
            'resolution': SummaryResolution.all,
            'fill': False,
        }

        bundle = GgoDistributionBundle(
            issued=self.get_issued(**kwargs),
            stored=self.get_stored(**kwargs),
            retired=self.get_retired(**kwargs),
            expired=self.get_expired(**kwargs),
            inbound=self.get_inbound(**kwargs),
            outbound=self.get_outbound(**kwargs),
        )

        return GetGgoDistributionsResponse(
            success=True,
            distributions=bundle,
        )

    def get_issued(self, **kwargs):
        """
        :param sqlalchemy.orm.Session session:
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_ggo_summary,
            category=GgoCategory.ISSUED,
            **kwargs,
        ))

    def get_stored(self, **kwargs):
        """
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_ggo_summary,
            category=GgoCategory.STORED,
            **kwargs,
        ))

    def get_retired(self, **kwargs):
        """
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_ggo_summary,
            category=GgoCategory.RETIRED,
            **kwargs,
        ))

    def get_expired(self, **kwargs):
        """
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_ggo_summary,
            category=GgoCategory.EXPIRED,
            **kwargs,
        ))

    def get_inbound(self, **kwargs):
        """
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_transfer_summary,
            direction=TransferDirection.INBOUND,
            **kwargs,
        ))

    def get_outbound(self, **kwargs):
        """
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_transfer_summary,
            direction=TransferDirection.OUTBOUND,
            **kwargs,
        ))

    def get_distributions(self, get_summary_groups_func):
        """
        :param function get_summary_groups_func: A function which returns a
            list of SummaryGroup objects
        :rtype: GgoDistribution
        """
        distribution = GgoDistribution()

        groups, labels = get_summary_groups_func()

        for summary_group in groups:
            distribution.technologies.append(GgoTechnology(
                technology=summary_group.group[0],
                amount=sum(summary_group.values),
            ))

        return distribution

    def get_transfer_summary(self, user, session, direction,
                             resolution, begin_range, utc_offset, fill):
        """
        Get either Issued, Stored, Retired and Expired from GgoSummary.

        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :param TransferDirection direction:
        :param SummaryResolution resolution:
        :param DateTimeRange begin_range:
        :param int utc_offset:
        :param bool fill:
        :rtype: List[SummaryGroup]
        """
        query = TransactionQuery(session) \
            .begins_within(begin_range)

        if direction is TransferDirection.INBOUND:
            query = query.received_by_user(user)
        elif direction is TransferDirection.OUTBOUND:
            query = query.sent_by_user(user)
        else:
            query = query.sent_or_received_by_user(user)

        summary = query.get_summary(
            resolution=resolution,
            utc_offset=utc_offset,
            grouping=['technology'],
        )

        return summary.groups, summary.labels

        # response = account_service.get_transfer_summary(
        #     token=token,
        #     request=acc.GetTransferSummaryRequest(
        #         utc_offset=utc_offset,
        #         direction=direction,
        #         resolution=resolution,
        #         fill=fill,
        #         grouping=[acc.SummaryGrouping.TECHNOLOGY],
        #         filters=acc.TransferFilters(
        #             begin_range=begin_range,
        #         ),
        #     ),
        # )
        #
        # return response.groups, response.labels

    def get_ggo_summary(self, user, session, category, resolution,
                        begin_range, utc_offset, fill):
        """
        Get either Issued, Stored, Retired and Expired from GgoSummary.

        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :param acc.GgoCategory category:
        :param SummaryResolution resolution:
        :param DateTimeRange begin_range:
        :param int utc_offset:
        :param bool fill:
        :rtype: (List[SummaryGroup], List[str])
        """
        query = GgoQuery(session) \
            .belongs_to(user) \
            .begins_within(begin_range) \
            .in_category(category)

        summary = query.get_summary(
            resolution=resolution,
            utc_offset=utc_offset,
            grouping=['technology'],
        )

        if fill:
            summary.fill(begin_range)

        return summary.groups, summary.labels


class GetGgoSummary(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetGgoSummaryRequest)
    Response = md.class_schema(GetGgoSummaryResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetGgoSummaryRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetGgoSummaryResponse
        """
        begin_range = DateTimeRange.from_date_range(request.date_range)
        resolution = get_resolution(begin_range.delta)

        query = GgoQuery(session) \
            .belongs_to(user) \
            .in_category(request.category) \
            .begins_within(begin_range)

        summary = query.get_summary(
            resolution=resolution,
            grouping=['technology'],
            utc_offset=request.utc_offset,
        )

        summary.fill(begin_range)

        return GetGgoSummaryResponse(
            success=True,
            labels=summary.labels,
            ggos=[DataSet(g.group[0], g.values) for g in summary.groups],
        )


class GetPeakMeasurement(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetPeakMeasurementRequest)
    Response = md.class_schema(GetPeakMeasurementResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetPeakMeasurementRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetPeakMeasurementResponse
        """
        measurement = MeasurementQuery(session) \
            .belongs_to(user) \
            .begins_within(DateTimeRange.from_date_range(request.date_range)) \
            .is_type(request.measurement_type) \
            .order_by(Measurement.amount.desc()) \
            .limit(1) \
            .one_or_none()

        return GetPeakMeasurementResponse(
            success=measurement is not None,
            measurement=measurement,
        )
