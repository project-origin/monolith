"""
Password hashing.
"""
import hashlib

from origin.config import SECRET


def password_hash(password):
    """
    :param str password:
    :rtype: str
    """
    return hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                               SECRET.encode('utf-8'), 100000).hex()
