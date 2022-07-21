from abc import abstractmethod

from wrapt import decorator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import \
    sessionmaker, scoped_session, configure_mappers, load_only, Query

from origin.config import SQL_DATABASE_URI, SQL_ALCHEMY_SETTINGS


ModelBase = declarative_base()


if SQL_DATABASE_URI:
    engine = create_engine(SQL_DATABASE_URI, **SQL_ALCHEMY_SETTINGS)
    configure_mappers()
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Session = scoped_session(factory)
else:
    from sqlalchemy.orm import Session


def make_session(*args, **kwargs):
    """
    Create a new SQLAlchemy session.

    :rtype: sqlalchemy.orm.Session
    """
    return Session(*args, **kwargs)


@decorator
def inject_session(wrapped, instance, args, kwargs):
    """
    Function decorator which injects a "session" named parameter
    if it doesn't already exists
    """
    session = kwargs.setdefault('session', make_session())
    try:
        return wrapped(*args, **kwargs)
    finally:
        session.close()


@decorator
def atomic(wrapped, instance, args, kwargs):
    """
    Function decorator which injects a "session" named parameter
    if it doesn't already exists, and wraps the function in an
    atomic transaction.
    """
    session = kwargs.setdefault('session', make_session())
    try:
        return_value = wrapped(*args, **kwargs)
    except:
        session.rollback()
        raise
    else:
        session.commit()
        return return_value


class SqlQuery(object):
    """ORM-level SQL construction class."""

    def __init__(self, session: Session, query: Query = None):
        self.session = session
        self.query = query or self._get_base_query()

    @abstractmethod
    def _get_base_query(self) -> Query:
        """Handle the error if the Query is bad."""
        raise NotImplementedError

    def __iter__(self):
        """Iterate though the query."""
        return iter(self.query)

    def __getattr__(self, name):
        """Get the name attribute for the object."""
        return getattr(self.query, name)

    def filter(self, *filters):
        """
        Apply the given filtering criterion (keyword) to a copy of the Query.

        Example usage::
            filter(Model.age==35, Model.country=='Denmark')

        :param filters: filtering criterion
        :return: Result of the filtering criterion
        """
        return self.__class__(self.session, self.query.filter(*filters))

    def filter_by(self, **filters):
        """
        Apply the given filtering criteria (keywords) to a copy of the Query.

        Example usage::
            filter_by(age=35, country='Denmark')

        :param filters: filtering criteria
        :return: Result of the filtering criteria
        """
        return self.__class__(self.session, self.query.filter_by(**filters))

    def only(self, *fields):
        """
        Narrows down the columns to select.

        TODO Example usage

        :param fields:
        :return:
        """
        return self.__class__(self.session, self.query.options(
            load_only(*fields)
        ))

    def get(self, field):
        """
        TODO.

        TODO Example usage

        :param field:
        :return: value for the field from the first result.
        """
        return self.only(field).scalar()

    def exists(self):
        """
        TODO.

        :return: True if result count is >= 1
        """
        return self.count() > 0
