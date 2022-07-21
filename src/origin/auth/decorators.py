from flask import request
from wrapt import decorator

from origin.db import make_session
from origin.http import Unauthorized
from origin.config import TOKEN_HEADER

from .queries import UserQuery
from .tokens import token_encoder


@decorator
def requires_login(wrapped, instance, args, kwargs):
    """
    :param wrapped:
    :param instance:
    :param args:
    :param kwargs:
    :return:
    """
    encoded_jwt = request.headers.get(TOKEN_HEADER)

    try:
        subject = token_encoder.decode(encoded_jwt)
    except token_encoder.DecodeError:
        raise Unauthorized()

    with make_session() as session:
        user = UserQuery(session) \
            .is_active() \
            .has_subject(subject) \
            .one_or_none()

    if user is None:
        raise Unauthorized()

    return wrapped(*args, user=user, **kwargs)
