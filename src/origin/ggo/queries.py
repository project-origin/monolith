import sqlalchemy as sa
from functools import lru_cache
from itertools import groupby
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, text, bindparam
from sqlalchemy.orm import joinedload, aliased
from datetime import datetime, timezone

from origin.db import SqlQuery
from origin.measurements.models import Measurement
from origin.meteringpoints import MeteringPoint
from origin.config import UNKNOWN_TECHNOLOGY_LABEL
from origin.technologies import Technology

from .models import Ggo, SplitTarget, SplitTransaction
from .schemas import SummaryResolution, SummaryGroup, GgoCategory


class GgoQuery(SqlQuery):
    """
    Abstraction around querying Ggo objects from the database,
    supporting cascade calls to combine filters.

    Usage example::

        query = GgoQuery(session) \
            .belongs_to('65e58f0b-62dd-40c2-a540-f773b0beed66') \
            .begins_at(datetime(2020, 1, 1, 0, 0))

        for ggo in query:
            pass

    Attributes not present on the GgoQuery class is redirected to
    SQLAlchemy's Query object, like count(), all() etc., for example::

        query = GgoQuery(session) \
            .belongs_to('65e58f0b-62dd-40c2-a540-f773b0beed66') \
            .begins_at(datetime(2020, 1, 1, 0, 0)) \
            .offset(100) \
            .limit(20) \
            .count()

    """

    begin = Measurement.begin

    def _get_base_query(self):
        return self.session.query(Ggo) \
            .outerjoin(Measurement, Measurement.id == Ggo.measurement_id) \
            .outerjoin(MeteringPoint, MeteringPoint.gsrn == Measurement.gsrn) \
            .options(joinedload(Ggo.measurement))

    def apply_filters(self, filters):
        """
        :param GgoFilters filters:
        :rtype: GgoQuery
        """
        q = self.query

        if filters.begin:
            q = q.filter(Ggo.begin == filters.begin.astimezone(timezone.utc))
        elif filters.begin_range:
            q = q.filter(Ggo.begin >= filters.begin_range.begin.astimezone(timezone.utc))
            q = q.filter(Ggo.begin <= filters.begin_range.end.astimezone(timezone.utc))
        # if filters.address:
        #     q = q.filter(Ggo.address.in_(filters.address))
        if filters.sector:
            q = q.filter(MeteringPoint.sector.in_(filters.sector))
        if filters.tech_code:
            q = q.filter(MeteringPoint.tech_code.in_(filters.tech_code))
        if filters.fuel_code:
            q = q.filter(MeteringPoint.fuel_code.in_(filters.fuel_code))
        if filters.issue_gsrn:
            q = q.filter(Ggo.issue_gsrn.in_(filters.issue_gsrn))
        if filters.retire_gsrn:
            q = q.filter(Ggo.retire_gsrn.in_(filters.retire_gsrn))
        # if filters.retire_address:
        #     q = q.filter(Ggo.retire_address.in_(filters.retire_address))

        new_query = self.__class__(self.session, q)

        if filters.category == GgoCategory.ISSUED:
            new_query = new_query.is_issued(True)
        elif filters.category == GgoCategory.STORED:
            new_query = new_query.is_stored(True).is_expired(False)
        elif filters.category == GgoCategory.RETIRED:
            new_query = new_query.is_retired(True)
        elif filters.category == GgoCategory.EXPIRED:
            new_query = new_query.is_stored(True).is_expired(True)

        return new_query

    def in_category(self, category):
        """
        Only include the Ggo with a specific category.

        :param GgoCategory category:
        :rtype: GgoQuery
        """
        if category == GgoCategory.ISSUED:
            return self.is_issued(True)
        elif category == GgoCategory.STORED:
            return self.is_stored(True).is_expired(False)
        elif category == GgoCategory.RETIRED:
            return self.is_retired(True)
        elif category == GgoCategory.EXPIRED:
            return self.is_stored(True).is_expired(True)

    def has_id(self, id):
        """
        Only include the Ggo with a specific ID.

        :param int id:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.id == id,
        ))

    def has_public_id(self, public_id):
        """
        Only include the Ggo with a specific public_id.

        :param str public_id:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.public_id == public_id,
        ))

    def belongs_to(self, user):
        """
        Only include GGOs which belong to the user identified by
        the provided sub (subject).

        :param origin.auth.User user:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.subject == user.subject,
        ))

    def begins_at(self, begin):
        """
        Only include GGOs which begins at the provided datetime.

        :param datetime begin:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.begin == begin.astimezone(timezone.utc),
        ))

    def begins_within(self, begin_range):
        """
        Only include GGOs which begins within the provided datetime
        range (both begin and end are included).

        :param DateTimeRange begin_range:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(sa.and_(
            Ggo.begin >= begin_range.begin.astimezone(timezone.utc),
            Ggo.begin <= begin_range.end.astimezone(timezone.utc),
        )))

    def has_gsrn(self, gsrn):
        """
        Only include GGOs which were issued to the MeteringPoint
        identified with the provided GSRN number.

        :param str gsrn:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            MeteringPoint.gsrn == gsrn,
        ))

    def is_issued(self, value=True):
        """
        Include or exclude GGOs which were issued from producing energy,
        ie. is not a result og transferring/splitting.

        :param bool value:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.issued.is_(value),
        ))

    def is_stored(self, value=True):
        """
        Include or exclude GGOs which are currently stored.

        :param bool value:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.stored.is_(value),
        ))

    def is_retired(self, value=True):
        """
        Include or exclude GGOs which have been retired.

        :param bool value:
        :rtype: GgoQuery
        """
        filters = [Ggo.retired.is_(value)]

        # if value is True:
        #     filters.append(Ggo.retire_gsrn.isnot(None))
        #     filters.append(Ggo.retire_address.isnot(None))
        # else:
        #     filters.append(Ggo.retire_gsrn.is_(None))
        #     filters.append(Ggo.retire_address.is_(None))

        return self.__class__(self.session, self.query.filter(*filters))

    def is_retired_to_measurement(self, measurement):
        """
        Only include GGOs which have been retired to a measurement address.

        :param Measurement measurement:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.retired.is_(True),
            Ggo.retire_gsrn.isnot(None),
            Ggo.retire_measurement_id == measurement.id,
        ))

    def is_retired_to_gsrn(self, gsrn):
        """
        Only include GGOs which have been retired to a GSRN number.

        :param str gsrn:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.retired.is_(True),
            Ggo.retire_measurement_id.isnot(None),
            Ggo.retire_gsrn == gsrn,
        ))

    def is_retired_to_any_gsrn(self, gsrn):
        """
        Only include GGOs which have been retired to any of the
        provided GSRN numbers.

        :param list[str] gsrn:
        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.retire_gsrn.in_(gsrn),
        ))

    def is_expired(self, value=True):
        """
        Include or exclude GGOs which are expired.

        :param bool value:
        :rtype: GgoQuery
        """
        if value is True:
            cond = Ggo.expire_time <= sa.func.now()
        elif value is False:
            cond = Ggo.expire_time > sa.func.now()
        else:
            raise RuntimeError('Should NOT have happened!')

        return self.__class__(self.session, self.query.filter(cond))

    # def is_synchronized(self, value=True):
    #     """
    #     Include or exclude GGOs which are synchronized on the ledger.
    #
    #     :param bool value:
    #     :rtype: GgoQuery
    #     """
    #     return self.__class__(self.session, self.query.filter(
    #         Ggo.synchronized.is_(value),
    #     ))
    #
    # def is_locked(self, value=True):
    #     """
    #     Include or exclude GGOs which are locked by operations on the ledger.
    #
    #     :param bool value:
    #     :rtype: GgoQuery
    #     """
    #     return self.__class__(self.session, self.query.filter(
    #         Ggo.locked.is_(value),
    #     ))

    def is_tradable(self):
        """
        Only include GGOs which are currently tradable (or retireable).

        :rtype: GgoQuery
        """
        return self \
            .is_stored(True) \
            .is_expired(False) \
            .is_retired(False)

    def is_retirable(self):
        """
        Only include GGOs which are currently retireable.

        :rtype: GgoQuery
        """
        return self.is_tradable()

    def has_emissions(self):
        """
        Only include GGOs which have emission data.

        :rtype: GgoQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.emissions.isnot(None),
        ))

    def get_total_amount(self):
        """
        Returns the total amount of the result set.

        :rtype: int
        """
        total_amount = self.session.query(
            func.sum(self.query.subquery().c.amount)).scalar()
        return total_amount if total_amount is not None else 0

    def get_distinct_begins(self):
        """
        Returns a list of all distinct begins in the result set.

        :rtype: list[datetime]
        """
        return [row[0] for row in self.session.query(
            self.query.subquery().c.begin.distinct())]

    def get_summary(self, resolution, grouping, utc_offset=0):
        """
        Returns a summary of the result set.

        :param SummaryResolution resolution:
        :param list[str] grouping:
        :param int utc_offset:
        :rtype: GgoSummary
        """
        return GgoSummary(
            self.session, self, resolution, grouping, utc_offset)


class TransactionQuery(GgoQuery):
    """
    The same as GgoQuery except it only includes GGOs which have
    been transferred.
    """

    parent_ggo = aliased(Ggo, name='parent')
    parent_ggo_meteringpoint = aliased(Ggo, name='parent')

    def __init__(self, session, q=None):
        """
        :param sa.orm.Session session:
        :param sa.orm.Query q:
        """
        if q is None:
            q = session.query(Ggo) \
                .join(SplitTarget, SplitTarget.ggo_id == Ggo.id) \
                .join(SplitTransaction, SplitTransaction.id == SplitTarget.transaction_id) \
                .join(self.parent_ggo, self.parent_ggo.id == SplitTransaction.parent_ggo_id) \
                .filter(Ggo.subject != self.parent_ggo.subject)

        super(TransactionQuery, self).__init__(session, q)

    def apply_filters(self, filters):
        """
        :param TransferFilters filters:
        :rtype: TransactionQuery
        """
        q = super(TransactionQuery, self).apply_filters(filters)

        if filters.reference:
            q = q.has_any_reference(filters.reference)

        return q

    def sent_by_user(self, user):
        """
        TODO

        :param User user:
        :rtype: TransactionQuery
        """
        return self.__class__(self.session, self.query.filter(
            self.parent_ggo.subject == user.subject,
        ))

    def received_by_user(self, user):
        """
        TODO

        :param User user:
        :rtype: TransactionQuery
        """
        return self.__class__(self.session, self.query.filter(
            Ggo.subject == user.subject,
        ))

    def sent_or_received_by_user(self, user):
        """
        TODO

        :param User user:
        :rtype: TransactionQuery
        """
        return self.__class__(self.session, self.query.filter(sa.or_(
            self.parent_ggo.subject == user.subject,
            Ggo.subject == user.subject,
        )))

    def has_reference(self, reference):
        """
        :param str reference:
        :rtype: TransactionQuery
        """
        return self.__class__(self.session, self.query.filter(
            SplitTarget.reference == reference,
        ))

    def has_any_reference(self, references):
        """
        :param list[str] references:
        :rtype: TransactionQuery
        """
        return self.__class__(self.session, self.query.filter(
            SplitTarget.reference.in_(references),
        ))


class GgoSummary(object):
    """
    Implements a summary/aggregation of GGOs.

    Provided a GgoQuery, this class compiles together a list of
    SummaryGroups, where each group is defined by the "grouping" parameter.
    The aggregated data is based on the result set of the query provided.
    It essentially works by wrapping a SQL "GROUP BY" statement.

    The parameter "resolution" defined the returned data resolution.
    Call .fill() before accessing .labels or .groups to fill gaps in data.
    """

    GROUPINGS = (
        'begin',
        'sector',
        'technology',
        'technologyCode',
        'fuelCode',
    )

    RESOLUTIONS_POSTGRES = {
        SummaryResolution.hour: 'YYYY-MM-DD HH24:00',
        SummaryResolution.day: 'YYYY-MM-DD',
        SummaryResolution.month: 'YYYY-MM',
        SummaryResolution.year: 'YYYY',
    }

    RESOLUTIONS_PYTHON = {
        SummaryResolution.hour: '%Y-%m-%d %H:00',
        SummaryResolution.day: '%Y-%m-%d',
        SummaryResolution.month: '%Y-%m',
        SummaryResolution.year: '%Y',
    }

    LABEL_STEP = {
        SummaryResolution.hour: relativedelta(hours=1),
        SummaryResolution.day: relativedelta(days=1),
        SummaryResolution.month: relativedelta(months=1),
        SummaryResolution.year: relativedelta(years=1),
        SummaryResolution.all: None,
    }

    ALL_TIME_LABEL = 'All-time'

    def __init__(self, session, query, resolution, grouping, utc_offset=0):
        """
        :param sa.orm.Session session:
        :param GgoQuery query:
        :param SummaryResolution resolution:
        :param list[str] grouping:
        :param int utc_offset:
        """
        self.session = session
        self.query = query
        self.resolution = resolution
        self.grouping = grouping
        self.utc_offset = utc_offset
        self.fill_range = None

    def fill(self, fill_range):
        """
        :param DateTimeRange fill_range:
        """
        self.fill_range = fill_range

    @property
    def labels(self):
        """
        :rtype list[str]:
        """
        if self.resolution == SummaryResolution.all:
            return [self.ALL_TIME_LABEL]
        if self.fill_range is None:
            return sorted(set(label for label, *g, amount in self.raw_results))
        else:
            format = self.RESOLUTIONS_PYTHON[self.resolution]
            step = self.LABEL_STEP[self.resolution]
            begin = self.fill_range.begin
            labels = []

            while begin <= self.fill_range.end:
                labels.append(begin.strftime(format))
                begin += step

            return labels

    @property
    def groups(self):
        """
        :rtype list[SummaryGroup]:
        """
        groups = []

        for group, results in groupby(self.raw_results, lambda x: x[1:-1]):
            items = {label: amount for label, *g, amount in results}
            groups.append(SummaryGroup(
                group=group,
                values=[items.get(label, None) for label in self.labels],
            ))

        return groups

    @property
    @lru_cache()
    def raw_results(self):
        """
        TODO
        """
        select = []
        groups = []
        orders = []

        s = self.query.subquery()

        q = self.session.query(
                s,
                func.coalesce(Technology.technology, UNKNOWN_TECHNOLOGY_LABEL).label('technology')
            ) \
            .outerjoin(Technology, sa.and_(
                Technology.tech_code == s.c.tech_code,
                Technology.fuel_code == s.c.fuel_code,
            )).subquery()

        if self.utc_offset is not None:
            begin = q.c.begin + text("INTERVAL '%d HOURS'" % self.utc_offset)
        else:
            begin = q.c.begin

        # -- Resolution ------------------------------------------------------

        if self.resolution == SummaryResolution.all:
            select.append(bindparam('label', self.ALL_TIME_LABEL))
        else:

            select.append(func.to_char(begin, self.RESOLUTIONS_POSTGRES[self.resolution]).label('resolution'))
            groups.append('resolution')

        # -- Grouping ------------------------------------------------------------

        for group in self.grouping:
            if group == 'begin':
                groups.append(begin)
                select.append(begin)
                orders.append(begin)
            elif group == 'sector':
                groups.append(q.c.sector)
                select.append(q.c.sector)
                orders.append(q.c.sector)
            elif group == 'technology':
                groups.append(q.c.technology)
                select.append(q.c.technology)
                orders.append(q.c.technology)
            elif group == 'technologyCode':
                groups.append(q.c.tech_code)
                select.append(q.c.tech_code)
                orders.append(q.c.tech_code)
            elif group == 'fuelCode':
                groups.append(q.c.fuel_code)
                select.append(q.c.fuel_code)
                orders.append(q.c.fuel_code)
            else:
                raise RuntimeError('Invalid grouping: %s' % self.grouping)

        # -- Query ---------------------------------------------------------------

        select.append(func.sum(q.c.amount))

        return self.session \
            .query(*select) \
            .group_by(*groups) \
            .order_by(*orders) \
            .all()
