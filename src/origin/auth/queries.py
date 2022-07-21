from sqlalchemy import or_

from origin.db import SqlQuery
from .hashing import password_hash

from .models import User


class UserQuery(SqlQuery):
    """
    Abstraction around querying User objects from the database,
    supporting cascade calls to combine filters.

    Usage example::

        query = UserQuery(session) \
            .has_gsrn('123456789012345') \
            .should_refresh_token()

        for user in query:
            pass

    Attributes not present on the UserQuery class is redirected to
    SQLAlchemy's Query object, like count(), all() etc., for example::

        query = UserQuery(session) \
            .has_gsrn('123456789012345') \
            .should_refresh_token() \
            .offset(100) \
            .limit(20) \
            .count()

    """

    def _get_base_query(self):
        return self.session.query(User)
        # return self.session.query(User).options(raiseload(User.metering_points))

    def is_active(self):
        """
        :rtype: UserQuery
        """
        return self.__class__(self.session, self.query.filter(
            User.active.is_(True),
        ))

    def has_email(self, email):
        """
        Only include the user with a specific ID.

        :param str email:
        :rtype: UserQuery
        """
        return self.__class__(self.session, self.query.filter(
            User.email == email,
        ))

    def has_password(self, password):
        """
        Only include the user with a specific ID.

        :param str password:
        :rtype: UserQuery
        """
        return self.__class__(self.session, self.query.filter(
            User.password == password_hash(password),
        ))

    def has_id(self, id):
        """
        Only include the user with a specific ID.

        :param int id:
        :rtype: UserQuery
        """
        return self.__class__(self.session, self.query.filter(
            User.id == id,
        ))

    def has_subject(self, subject):
        """
        Only include the user with a specific subject.

        :param str subject:
        :rtype: UserQuery
        """
        return self.__class__(self.session, self.query.filter(
            User.subject == subject,
        ))

    def has_gsrn(self, gsrn):
        """
        Only include users which owns the MeteringPoint identified with
        the provided GSRN number.

        :param str gsrn:
        :rtype: UserQuery
        """
        return self.__class__(self.session, self.query.filter(
            User.metering_points.any(gsrn=gsrn),
        ))

    def starts_with(self, query):
        """
        :param str query:
        :rtype: UserQuery
        """
        return self.__class__(self.session, self.query.filter(
            or_(
                User.name.ilike('%s%%' % query),
                User.company.ilike('%s%%' % query),
            )
        ))

    def exclude(self, user):
        """
        :param User user:
        :rtype: UserQuery
        """
        return self.__class__(self.session, self.query.filter(
            User.subject != user.subject,
        ))
