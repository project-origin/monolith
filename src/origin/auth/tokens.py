import jwt

from origin.config import SECRET


class TokenEncoder:
    """Generic helper-class to encode/decode dataclasses to and from JWT."""

    class EncodeError(Exception):
        """Raised when encoding fails."""

        pass

    class DecodeError(Exception):
        """Raised when decoding fails."""
        pass

    HS256 = 'HS256'
    RS256 = 'RS256'

    def __init__(self, secret, alg=HS256):
        self.secret = secret
        self.alg = alg

    def encode(self, subject):
        """
        Encode JWT.

        :param str subject: User subject
        :return: Encoded jwt
        """
        return jwt.encode(
            key=self.secret,
            algorithm=self.alg,
            payload={
                'subject': subject,
            },
        )

    def decode(self, encoded_jwt: str):
        """
        Decode JWT.

        :param encoded_jwt: Encoded JWT to be decoded
        :return: User subject
        """
        try:
            payload = jwt.decode(
                jwt=encoded_jwt,
                key=self.secret,
                algorithms=[self.alg],
            )
        except jwt.DecodeError as e:
            raise self.DecodeError(str(e))

        return payload['subject']


# -- Singleton ---------------------------------------------------------------


token_encoder = TokenEncoder(secret=SECRET)
