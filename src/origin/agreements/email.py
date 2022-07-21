import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail, To

from origin.config import (
    EMAIL_FROM_ADDRESS,
    EMAIL_FROM_NAME,
    SENDGRID_API_KEY,
    FRONTEND_URL,
)


INVITATION_RECEIVED_SUBJECT = 'You have received a GGO transfer proposal'
INVITATION_RECEIVED_TEMPLATE = """Dear %(name)s

You have received a GGO transfer agreement proposal.

Log in to your account to respond the proposal.

%(link)s
"""


INVITATION_ACCEPTED_SUBJECT = 'Your GGO transfer proposal was accepted'
INVITATION_ACCEPTED_TEMPLATE = """Dear %(name)s

%(counterpart)s has accepted your GGO transfer agreement.

Log in to your account to keep track of transfers.

%(link)s
"""


INVITATION_DECLINED_SUBJECT = 'Your GGO transfer proposal was declined'
INVITATION_DECLINED_TEMPLATE = """Dear %(name)s

%(counterpart)s has declined your GGO transfer agreement.

Log in to your account to propose other agreements.

%(link)s
"""


def _send_email(user, subject, body):
    """
    :param originexample.auth.User user:
    :param str body:
    :rtype: bool
    """
    from_email = Email(EMAIL_FROM_ADDRESS, EMAIL_FROM_NAME)
    to_email = To(user.email, user.name)
    content = Content('text/plain', body)
    mail = Mail(from_email, to_email, subject, content)

    client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    response = client.client.mail.send.post(request_body=mail.get())

    return response.status_code in (200, 201, 202)


def send_invitation_received_email(agreement):
    """
    :param originexample.agreements.TradeAgreement agreement:
    :rtype: bool
    """
    body = INVITATION_RECEIVED_TEMPLATE % {
        'sub': agreement.user_proposed_to.subject,
        'name': agreement.user_proposed_to.name,
        'company': agreement.user_proposed_to.company,
        'link': FRONTEND_URL,
    }

    return _send_email(
        user=agreement.user_proposed_to,
        subject=INVITATION_RECEIVED_SUBJECT,
        body=body,
    )


def send_invitation_accepted_email(agreement):
    """
    :param originexample.agreements.TradeAgreement agreement:
    :rtype: bool
    """
    body = INVITATION_ACCEPTED_TEMPLATE % {
        'name': agreement.user_proposed.name,
        'counterpart': agreement.user_proposed_to.company,
        'link': FRONTEND_URL,
    }

    return _send_email(
        user=agreement.user_proposed,
        subject=INVITATION_ACCEPTED_SUBJECT,
        body=body,
    )


def send_invitation_declined_email(agreement):
    """
    :param originexample.agreements.TradeAgreement agreement:
    :rtype: bool
    """
    body = INVITATION_DECLINED_TEMPLATE % {
        'name': agreement.user_proposed.name,
        'counterpart': agreement.user_proposed_to.company,
        'link': FRONTEND_URL,
    }

    return _send_email(
        user=agreement.user_proposed,
        subject=INVITATION_DECLINED_SUBJECT,
        body=body,
    )
