import sys
import csv
import json
import random
from uuid import uuid4

import click
from click import echo, confirm, Abort
from cloup import group, command, option, Choice

from origin.db import atomic, inject_session

from .models import User
from .queries import UserQuery
from .hashing import password_hash


# -- Commands ----------------------------------------------------------------
from .tokens import token_encoder


@command()
@option(
    '--subject',
    type=str,
    required=True,
    prompt=True,
    default=lambda: str(uuid4()),
)
@option(
    '--name',
    type=str,
    required=True,
    prompt=True,
    default=lambda: f'New user #{random.randint(1000, 9999)}',
)
@option(
    '--company',
    type=str,
    required=True,
    prompt=True,
    default='The Pizza Bar',
)
@option(
    '--email',
    type=str,
    required=True,
    prompt=True,
    default=f'random{random.randint(9999, 99999)}@foo.bar',
)
@option(
    '--password',
    type=str,
    required=True,
    prompt=True,
    default='12345678',
)
@option(
    '--active',
    is_flag=True,
    prompt=True,
)
@atomic
def create_user(subject, name, company, email, password, active, session):
    """
    Create a new user
    """
    session.add(User(
        subject=subject,
        active=active,
        email=email,
        password=password_hash(password),
        name=name,
        company=company,
    ))


@command()
@option(
    '--subject',
    type=str,
    required=True,
    prompt=True,
    help='User subject',
)
@option(
    '--yes',
    type=bool,
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation',
)
@atomic
def delete_user(subject, yes, session):
    """
    Delete a user
    """
    user = UserQuery(session) \
        .has_subject(subject) \
        .one_or_none()

    if user is None:
        echo(f'User with subject "{subject}" not found')
        raise Abort()

    if yes is not True:
        if not confirm(f'Really delete user "{user.name}"?', default=True):
            raise Abort()

    session.delete(user)
    session.flush()

    echo(f'User "{user.name}" deleted!')


@command()
@option(
    '--out',
    type=Choice(('csv', 'json')),
    required=True,
    default='json',
    help='Output format',
)
@inject_session
def list_users(out, session):
    """
    List users
    """
    users = UserQuery(session).all()

    keys = (
        'subject',
        'created',
        'active',
        'email',
        'phone',
        'name',
        'company',
    )

    objects = [
        {key: getattr(user, key) for key in keys}
        for user in users
    ]

    if out == 'csv':
        writer = csv.DictWriter(
            sys.stdout, extrasaction='ignore', fieldnames=keys)
        writer.writeheader()
        writer.writerows(objects)

    elif out == 'json':
        print(json.dumps(objects, indent=4, sort_keys=True, default=str))


@command()
@option(
    '--subject',
    type=str,
    required=True,
    prompt=True,
    help='User subject',
)
@atomic
def activate_user(subject, session):
    """
    Activate a user
    """
    user = UserQuery(session) \
        .has_subject(subject) \
        .one_or_none()

    if user is None:
        echo(f'User with subject "{subject}" not found')
        raise Abort()

    if user.active:
        echo(f'User with subject "{subject}" is already activated')
        raise Abort()

    user.active = True

    session.flush()

    echo(f'User "{user.name}" activated!')


@command()
@option(
    '--subject',
    type=str,
    required=True,
    prompt=True,
    help='User subject',
)
@atomic
def deactivate_user(subject, session):
    """
    Deactivate a user
    """
    user = UserQuery(session) \
        .has_subject(subject) \
        .one_or_none()

    if user is None:
        echo(f'User with subject "{subject}" not found')
        raise Abort()

    if not user.active:
        echo(f'User with subject "{subject}" is already deactivated')
        raise Abort()

    user.active = False

    session.flush()

    echo(f'User "{user.name}" deactivated!')


@command()
@option(
    '--subject',
    type=str,
    required=True,
    prompt=True,
    help='User subject',
)
def create_token(subject):
    """
    Creates an HTTP API bearer token
    """
    click.echo(token_encoder.encode(subject))


# -- Group -------------------------------------------------------------------


@group()
def users_group() -> None:
    """
    Manage users
    """
    pass


users_group.add_command(create_user, 'create')
users_group.add_command(delete_user, 'delete')
users_group.add_command(list_users, 'list')
users_group.add_command(activate_user, 'activate')
users_group.add_command(deactivate_user, 'deactivate')
users_group.add_command(create_token, 'token')
