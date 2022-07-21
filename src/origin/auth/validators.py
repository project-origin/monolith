"""
Additional common schema validators for JSON-to-model validation.
Plugs into Marshmallow's validation model and can be used in
conjunction with the marshmallow and marshmallow-dataclass libraries.
"""
from marshmallow import ValidationError

from origin.db import inject_session

from .queries import UserQuery


@inject_session
def subject_exists(sub, session, *args, **kwargs):
    """
    Validates that a user exists with the provided subject.
    """
    user = UserQuery(session) \
        .is_active() \
        .has_subject(sub) \
        .one_or_none()

    if user is None:
        raise ValidationError('No user exists with subject: %s' % sub)
