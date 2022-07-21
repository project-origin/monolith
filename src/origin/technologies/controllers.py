import marshmallow_dataclass as md

from origin.http import Controller
from origin.db import inject_session

from .models import Technology
from .schemas import GetTechnologiesResponse


class GetTechnologies(Controller):
    """
    Returns a list of all Technology objects.
    """
    Response = md.class_schema(GetTechnologiesResponse)

    @inject_session
    def handle_request(self, session):
        """
        :param sqlalchemy.orm.Session session:
        :rtype: GetTechnologiesResponse
        """
        return GetTechnologiesResponse(
            success=True,
            technologies=session.query(Technology).all(),
        )
