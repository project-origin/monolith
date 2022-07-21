import re
import sendgrid
import marshmallow_dataclass as md
from sendgrid.helpers.mail import (
    Email, Content, Mail, To, Attachment, FileContent,
    FileName, FileType, Disposition, Header, ReplyTo
)

from origin.http import Controller, BadRequest
from origin.auth import User, requires_login
from origin.config import (
    EMAIL_TO_ADDRESS,
    EMAIL_FROM_ADDRESS,
    EMAIL_FROM_NAME,
    EMAIL_PREFIX,
    SENDGRID_API_KEY,
)

from .models import (
    SubmitSupportEnquiryRequest,
    SubmitSupportEnquiryResponse,
)


FILE_SOURCE_PATTERN = re.compile(r'data:(.+);base64,(.+)')


SUPPORT_ENQUIRY_EMAIL_TEMPLATE = """Support enquiry sent from ElOverblik.dk:
------------------------------------------------------------------------------
Sender: %(name)s <%(email)s>
Company: %(company)s
Phone: %(phone)s
E-mail: %(email)s
User ID: %(sub)s
Link: %(link)s
------------------------------------------------------------------------------

%(message)s"""


class SubmitSupportEnquiry(Controller):
    """
    TODO
    """
    Request = md.class_schema(SubmitSupportEnquiryRequest)
    Response = md.class_schema(SubmitSupportEnquiryResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param SubmitSupportEnquiryRequest request:
        :param User user:
        :rtype: bool
        """
        body = SUPPORT_ENQUIRY_EMAIL_TEMPLATE % {
            'sub': user.sub,
            'email': request.email,
            'name': user.name,
            'company': user.company,
            'link': request.link,
            'phone': request.phone,
            'message': request.message,
        }

        from_email = Email(EMAIL_FROM_ADDRESS, EMAIL_FROM_NAME)
        to_email = To(EMAIL_TO_ADDRESS)
        subject = f'{EMAIL_PREFIX}{request.subject_type} - {request.subject}'
        content = Content('text/plain', body)
        mail = Mail(from_email, to_email, subject, content)
        mail.reply_to = ReplyTo(request.email, user.name)

        # Recipe (CC) to sender)
        if request.recipe:
            mail.add_cc(To(request.email))

        # File attachment
        if request.file_name and request.file_source:
            mail.attachment = self.create_attachment(
                request.file_name, request.file_source)

        client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = client.client.mail.send.post(request_body=mail.get())

        return response.status_code in (200, 201, 202)

    def create_attachment(self, file_name, file_source):
        match = FILE_SOURCE_PATTERN.match(file_source)
        if match is None:
            raise BadRequest('Bad file attachment')

        file_type, file_content = match.groups()

        return Attachment(
            FileContent(file_content),
            FileName(file_name.split('\\')[-1]),
            FileType(file_type),
            Disposition('attachment')
        )
