import pytz
import sqlalchemy as sa
from sqlalchemy import text, func

from origin.db import SqlQuery
from origin.auth import User

from .models import TradeAgreement, AgreementState


class AgreementQuery(SqlQuery):
    """
    TODO
    """
    def _get_base_query(self):
        return self.session.query(TradeAgreement)

    def has_id(self, agreement_id):
        """
        TODO unittest this

        :param int agreement_id:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.id == agreement_id,
        ))

    def has_public_id(self, public_id):
        """
        :param str public_id:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.public_id == public_id,
        ))

    def belongs_to(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            sa.or_(
                TradeAgreement.user_from_subject == user.subject,
                TradeAgreement.user_to_subject == user.subject,
            ),
        ))

    def is_proposed_by(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.user_proposed_subject == user.subject,
        ))

    def is_proposed_to(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.user_proposed_subject != user.subject,
            sa.or_(
                TradeAgreement.user_from_subject == user.subject,
                TradeAgreement.user_to_subject == user.subject,
            ),
        ))

    def is_awaiting_response_by(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.state == AgreementState.PENDING,
            TradeAgreement.user_proposed_subject != user.subject,
            sa.or_(
                TradeAgreement.user_from_subject == user.subject,
                TradeAgreement.user_to_subject == user.subject,
            ),
        ))

    def is_inbound_to(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.user_to_subject == user.subject,
        ))

    def is_outbound_from(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.user_from_subject == user.subject,
        ))

    def is_pending(self):
        """
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.state == AgreementState.PENDING,
        ))

    def is_accepted(self):
        """
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.state == AgreementState.ACCEPTED,
        ))

    def is_cancelled(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.state == AgreementState.CANCELLED,
        ))

    def is_cancelled_recently(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.cancelled >= text("NOW() - INTERVAL '14 DAYS'"),
        ))

    def is_declined(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.state == AgreementState.DECLINED,
        ))

    def is_declined_recently(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.declined >= text("NOW() - INTERVAL '14 DAYS'"),
        ))

    def is_limited_to_consumption(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.limit_to_consumption.is_(True),
        ))

    def is_active(self):
        """
        :rtype: AgreementQuery
        """
        return self.is_accepted()

    def is_operating_at(self, begin):
        """
        TODO unittest this

        :param datetime.datetime begin:
        :rtype: AgreementQuery
        """
        b = begin.astimezone(pytz.timezone('Europe/Copenhagen')).date()

        return AgreementQuery(self.session, self.query.filter(
            TradeAgreement.date_from <= b,
            TradeAgreement.date_to >= b,
        ))

    def is_elibigle_to_trade(self, ggo):
        """
        :param Ggo ggo:

        :rtype: AgreementQuery
        """
        b = ggo.begin.astimezone(pytz.timezone('Europe/Copenhagen')).date()

        filters = [
            TradeAgreement.date_from <= b,
            TradeAgreement.date_to >= b,
            # sa.or_(
            #     TradeAgreement.technologies.is_(None),
            #     TradeAgreement.technologies.any(ggo.technology),
            # ),
            sa.or_(
                TradeAgreement.facility_gsrn.is_(None),
                TradeAgreement.facility_gsrn == [],
                TradeAgreement.facility_gsrn.any(ggo.issue_gsrn),
            ),
        ]

        if ggo.issue_gsrn:
            filters.append(sa.or_(
                TradeAgreement.facility_gsrn.is_(None),
                TradeAgreement.facility_gsrn == [],
                TradeAgreement.facility_gsrn.any(ggo.issue_gsrn),
            ))
        else:
            filters.append(sa.or_(
                TradeAgreement.facility_gsrn.is_(None),
                TradeAgreement.facility_gsrn == [],
            ))

        return AgreementQuery(self.session, self.query.filter(*filters))

    def get_peiority_max(self):
        """
        Returns the highest transfer_priority within the result set, or None.

        TODO unittest this

        :rtype: int | None
        """
        return self.session.query(
            func.max(self.query.subquery().c.transfer_priority)
        ).scalar()
