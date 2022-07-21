import sqlalchemy as sa

from origin.db import SqlQuery
from origin.technologies import Technology

from .schemas import MeteringPointFilters
from .models import MeteringPoint, MeteringPointTag, MeteringPointType


class MeteringPointQuery(SqlQuery):
    """
    Abstraction around querying MeteringPoint objects from the database,
    supporting cascade calls to combine filters.

    Usage example::

        query = MeteringPoint(session) \
            .belongs_to('65e58f0b-62dd-40c2-a540-f773b0beed66') \
            .is_production()

        for meteringpoint in query:
            pass

    Attributes not present on the GgoQuery class is redirected to
    SQLAlchemy's Query object, like count(), all() etc., for example::

        query = MeteringPoint(session) \
            .belongs_to('65e58f0b-62dd-40c2-a540-f773b0beed66') \
            .is_production() \
            .offset(100) \
            .limit(20) \
            .count()
    """

    def _get_base_query(self):
        return self.session.query(MeteringPoint)

    def apply_filters(self, filters):
        """
        :param MeteringPointFilters filters:
        :rtype: FacilityQuery
        """
        q = self.query

        if filters.type:
            if isinstance(filters.type, str):
                q = q.filter(MeteringPoint.type == MeteringPointType(filters.type))
            else:
                q = q.filter(MeteringPoint.type == filters.type)
        if filters.gsrn:
            q = q.filter(MeteringPoint.gsrn.in_(filters.gsrn))
        if filters.sectors:
            q = q.filter(MeteringPoint.sector.in_(filters.sectors))
        if filters.tags:
            q = q.filter(*[MeteringPoint.tags.any(tag=t) for t in filters.tags])
        if filters.technology:
            q = q.filter(MeteringPoint.technology.has(Technology.technology == filters.technology))
        if filters.text:
            # SQLite doesn't support full text search, so this is the second
            # best solution (the only?) which enables us to perform both
            # production and test execution of this filtering option
            q = q.filter(sa.or_(
                MeteringPoint.gsrn.ilike('%%%s%%' % filters.text),
                MeteringPoint.name.ilike('%%%s%%' % filters.text),
                MeteringPoint.street_name.ilike('%%%s%%' % filters.text),
                MeteringPoint.city_name.ilike('%%%s%%' % filters.text),
            ))

        return self.__class__(self.session, q)

    def belongs_to(self, user):
        """
        Only include meteringpoints which belong to the user identified by
        the provided sub (subject).

        :param origin.auth.User user:
        :rtype: MeteringPointQuery
        """
        return self.__class__(self.session, self.query.filter(
            MeteringPoint.subject == user.subject,
        ))

    def has_public_id(self, public_id):
        """
        :param str public_id:
        :rtype: FacilityQuery
        """
        return self.__class__(self.session, self.query.filter(
            MeteringPoint.public_id == public_id,
        ))

    def has_gsrn(self, gsrn):
        """
        Only include the meteringpoint with the provided GSRN number.

        :param str gsrn:
        :rtype: MeteringPointQuery
        """
        return self.__class__(self.session, self.query.filter(
            MeteringPoint.gsrn == gsrn,
        ))

    def has_any_gsrn(self, gsrn):
        """
        :param list[str] gsrn:
        :rtype: MeteringPointQuery
        """
        return self.__class__(self.session, self.query.filter(
            MeteringPoint.gsrn.in_(gsrn),
        ))

    def is_type(self, type):
        """
        Only include meteringpoints of the provided type,
        ie. PRODUCTION or CONSUMPTION.

        :param MeteringPointType type:
        :rtype: MeteringPointQuery
        """
        return self.__class__(self.session, self.query.filter(
            MeteringPoint.type == type,
        ))

    def is_production(self):
        """
        Only include meteringpoints of type PRODUCTION.

        :rtype: MeteringPointQuery
        """
        return self.is_type(MeteringPointType.PRODUCTION)

    def is_consumption(self):
        """
        Only include meteringpoints of type CONSUMPTION.

        :rtype: MeteringPointQuery
        """
        return self.is_type(MeteringPointType.CONSUMPTION)

    def is_retire_receiver(self):
        """
        :rtype: FacilityQuery
        """
        return self.__class__(self.session, self.query.filter(
            MeteringPoint.retiring_priority.isnot(None),
        ))

    def is_eligible_to_retire(self, ggo):
        """
        :param Ggo ggo:
        :rtype: MeteringPointType
        """
        return self.__class__(self.session, self.query.filter(
            MeteringPoint.sector == ggo.sector,
            MeteringPoint.type == MeteringPointType.CONSUMPTION,
        ))

    def get_distinct_sectors(self):
        """
        :rtype: list[str]
        """
        return [row[0] for row in self.session.query(
            self.query.subquery().c.sector.distinct())]

    def get_distinct_gsrn(self):
        """
        :rtype: list[str]
        """
        return [row[0] for row in self.session.query(
            self.query.subquery().c.gsrn.distinct())]

    def get_distinct_tags(self):
        """
        :rtype: list[str]
        """
        ids = [f.id for f in self.query.all()]

        q = self.session \
            .query(MeteringPointTag.tag.distinct()) \
            .filter(MeteringPointTag.meteringpoint_id.in_(ids))

        return [row[0] for row in q.all()]

    # Backwards compatibility
    is_consumer = is_consumption
    is_producer = is_production
