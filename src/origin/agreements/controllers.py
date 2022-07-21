import marshmallow_dataclass as md
from functools import partial

from origin.auth import User, UserQuery, requires_login
from origin.db import inject_session, atomic
from origin.http import Controller
from origin.common import DateTimeRange, DataSet, SummaryResolution
from origin.config import SEND_AGREEMENT_INVITATION_EMAIL
from origin.ggo import TransactionQuery

from .helpers import get_resolution, update_transfer_priorities
from .queries import AgreementQuery
from .email import (
    send_invitation_received_email,
    send_invitation_accepted_email,
    send_invitation_declined_email,
)
from .models import TradeAgreement, AgreementDirection, AgreementState
from .schemas import (
    MappedTradeAgreement,
    GetAgreementListResponse,
    GetAgreementSummaryRequest,
    GetAgreementSummaryResponse,
    SubmitAgreementProposalRequest,
    SubmitAgreementProposalResponse,
    RespondToProposalRequest,
    CountPendingProposalsResponse,
    WithdrawProposalRequest,
    GetAgreementDetailsRequest,
    GetAgreementDetailsResponse,
    CancelAgreementRequest,
    SetTransferPriorityRequest,
)


# -- Controllers -------------------------------------------------------------


class AbstractAgreementController(Controller):
    def map_agreement_for(self, user, agreement):
        """
        :param TradeAgreement agreement:
        :param User user:
        :rtype: MappedTradeAgreement
        """
        if agreement.is_inbound_to(user):
            return self.map_inbound_agreement(agreement)
        elif agreement.is_outbound_from(user):
            return self.map_outbound_agreement(agreement)
        else:
            raise RuntimeError('This should NOT have happened!')

    def map_inbound_agreement(self, agreement):
        """
        :param TradeAgreement agreement:
        :rtype: MappedTradeAgreement
        """
        return MappedTradeAgreement(
            direction=AgreementDirection.INBOUND,
            state=agreement.state,
            public_id=agreement.public_id,
            counterpart_subject=agreement.user_from.subject,
            counterpart=agreement.user_from.company,
            date_from=agreement.date_from,
            date_to=agreement.date_to,
            amount=agreement.amount,
            unit=agreement.unit,
            amount_percent=agreement.amount_percent,
            technologies=agreement.technologies,
            reference=agreement.reference,
            limit_to_consumption=agreement.limit_to_consumption,
            proposal_note=agreement.proposal_note,
        )

    def map_outbound_agreement(self, agreement):
        """
        :param TradeAgreement agreement:
        :rtype: MappedTradeAgreement
        """
        if agreement.facility_gsrn:
            facilities = self.get_facilities(
                agreement.user_from, agreement.facility_gsrn)
        else:
            facilities = []

        return MappedTradeAgreement(
            direction=AgreementDirection.OUTBOUND,
            state=agreement.state,
            public_id=agreement.public_id,
            counterpart_subject=agreement.user_to.subject,
            counterpart=agreement.user_to.company,
            date_from=agreement.date_from,
            date_to=agreement.date_to,
            amount=agreement.amount,
            unit=agreement.unit,
            amount_percent=agreement.amount_percent,
            technologies=agreement.technologies,
            reference=agreement.reference,
            limit_to_consumption=agreement.limit_to_consumption,
            proposal_note=agreement.proposal_note,
            facilities=facilities,
        )

    @inject_session
    def get_facilities(self, user, facility_gsrn, session):
        """
        :param User user:
        :param list[str] facility_gsrn:
        :param Session session:
        :rtype: list[Facility]
        """
        return FacilityQuery(session) \
            .belongs_to(user) \
            .has_any_gsrn(facility_gsrn) \
            .all()


class GetAgreementList(AbstractAgreementController):
    """
    TODO
    """
    Response = md.class_schema(GetAgreementListResponse)

    @requires_login
    @inject_session
    def handle_request(self, user, session):
        """
        :param User user:
        :param Session session:
        :rtype: GetAgreementListResponse
        """

        # Invitations currently awaiting response by this user
        pending = AgreementQuery(session) \
            .is_proposed_to(user) \
            .is_pending() \
            .order_by(TradeAgreement.created.asc()) \
            .all()

        # Invitations sent by this user awaiting response by another user
        sent = AgreementQuery(session) \
            .is_proposed_by(user) \
            .is_pending() \
            .order_by(TradeAgreement.created.asc()) \
            .all()

        # Inbound agreements currently active
        inbound = AgreementQuery(session) \
            .is_inbound_to(user) \
            .is_accepted() \
            .order_by(TradeAgreement.created.asc()) \
            .all()

        # Outbound agreements currently active
        outbound = AgreementQuery(session) \
            .is_outbound_from(user) \
            .is_accepted() \
            .order_by(TradeAgreement.transfer_priority.asc()) \
            .all()

        # Formerly accepted agreements which has now been cancelled
        cancelled = AgreementQuery(session) \
            .belongs_to(user) \
            .is_cancelled() \
            .is_cancelled_recently() \
            .order_by(TradeAgreement.cancelled.desc()) \
            .all()

        # Formerly proposed agreements which has now been declined
        declined = AgreementQuery(session) \
            .belongs_to(user) \
            .is_declined() \
            .is_declined_recently() \
            .order_by(TradeAgreement.declined.desc()) \
            .all()

        map_agreement = partial(self.map_agreement_for, user)

        return GetAgreementListResponse(
            success=True,
            pending=list(map(map_agreement, pending)),
            sent=list(map(map_agreement, sent)),
            inbound=list(map(map_agreement, inbound)),
            outbound=list(map(map_agreement, outbound)),
            cancelled=list(map(map_agreement, cancelled)),
            declined=list(map(map_agreement, declined)),
        )


class GetAgreementDetails(AbstractAgreementController):
    """
    TODO
    """
    Request = md.class_schema(GetAgreementDetailsRequest)
    Response = md.class_schema(GetAgreementDetailsResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetAgreementDetailsRequest request:
        :param User user:
        :param Session session:
        :rtype: GetAgreementDetailsResponse
        """
        agreement = AgreementQuery(session) \
            .has_public_id(request.public_id) \
            .belongs_to(user) \
            .one_or_none()

        if agreement:
            agreement = self.map_agreement_for(user, agreement)

        return GetAgreementDetailsResponse(
            success=agreement is not None,
            agreement=agreement,
        )


class GetAgreementSummary(AbstractAgreementController):
    """
    TODO
    """
    Request = md.class_schema(GetAgreementSummaryRequest)
    Response = md.class_schema(GetAgreementSummaryResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetAgreementSummaryRequest request:
        :param origin.auth.User user:
        :param sqlalchemy.orm.Session session:
        :rtype: GetAgreementListResponse
        """
        if request.date_range:
            resolution = get_resolution(request.date_range.delta)
            begin_range = DateTimeRange.from_date_range(request.date_range)
            fill = True
        else:
            resolution = SummaryResolution.month
            begin_range = None
            fill = False

        query = TransactionQuery(session)

        # Specific agreement?
        if request.public_id:
            query = query.has_reference(request.public_id)

        # Transfer direction
        if request.direction is AgreementDirection.INBOUND:
            query = query.received_by_user(user)
        elif request.direction is AgreementDirection.OUTBOUND:
            query = query.sent_by_user(user)
        else:
            query = query.sent_or_received_by_user(user)

        if begin_range:
            query = query.begins_within(begin_range)

        summary = query.get_summary(
            resolution=resolution,
            utc_offset=request.utc_offset,
            grouping=['technology'],
        )

        if fill:
            summary.fill(begin_range)

        datasets = [DataSet(g.group[0], g.values) for g in summary.groups]

        return GetAgreementSummaryResponse(
            success=True,
            labels=summary.labels,
            ggos=datasets,
        )


class CancelAgreement(Controller):
    """
    TODO
    """
    Request = md.class_schema(CancelAgreementRequest)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param CancelAgreementRequest request:
        :param User user:
        :param Session session:
        :rtype: bool
        """
        agreement = AgreementQuery(session) \
            .has_public_id(request.public_id) \
            .belongs_to(user) \
            .one_or_none()

        if agreement:
            # Agreement must be cancelled and its transaction committed to
            # the database before updating transfer priorities, hence both
            # are executed in a transaction for themselves sequentially
            self.cancel_agreement(agreement.public_id, user)
            self.update_transfer_priorities(agreement.user_from)
            return True
        else:
            return False

    @atomic
    def cancel_agreement(self, public_id, user, session):
        """
        TODO
        """
        AgreementQuery(session) \
            .has_public_id(public_id) \
            .belongs_to(user) \
            .one() \
            .cancel()

    @atomic
    def update_transfer_priorities(self, *args, **kwargs):
        """
        TODO
        """
        update_transfer_priorities(*args, **kwargs)


class SetTransferPriority(Controller):
    """
    TODO
    """
    Request = md.class_schema(SetTransferPriorityRequest)

    @requires_login
    def handle_request(self, request, user):
        """
        :param SetTransferPriorityRequest request:
        :param User user:
        :rtype: bool
        """
        self.update_transfer_priorities(
            request.public_ids_prioritized, user)

        self.complete_priorities(user)

        return True

    @atomic
    def update_transfer_priorities(self, public_ids_prioritized, user, session):
        """
        :param list[str public_ids_prioritized:
        :param User user:
        :param Session session:
        :rtype: bool
        """
        agreements = AgreementQuery(session) \
            .is_outbound_from(user) \
            .is_accepted()

        # Initially remove priority for all agreements
        agreements.update({TradeAgreement.transfer_priority: None})

        # Set priorities in the order they were provided
        for i, public_id in enumerate(public_ids_prioritized):
            agreements \
                .has_public_id(public_id) \
                .update({TradeAgreement.transfer_priority: i})

        return True

    @atomic
    def complete_priorities(self, *args, **kwargs):
        """
        TODO
        """
        update_transfer_priorities(*args, **kwargs)


# -- Proposals ---------------------------------------------------------------


class SubmitAgreementProposal(Controller):
    """
    TODO
    """
    Request = md.class_schema(SubmitAgreementProposalRequest)
    Response = md.class_schema(SubmitAgreementProposalResponse)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param SubmitAgreementProposalRequest request:
        :param User user:
        :param Session session:
        :rtype: SubmitAgreementProposalResponse
        """
        counterpart = UserQuery(session) \
            .is_active() \
            .has_subject(request.counterpart_subject) \
            .exclude(user) \
            .one_or_none()

        if not counterpart:
            return SubmitAgreementProposalResponse(success=False)

        if request.direction == AgreementDirection.INBOUND:
            user_from = counterpart
            user_to = user
        elif request.direction == AgreementDirection.OUTBOUND:
            user_from = user
            user_to = counterpart
        else:
            raise RuntimeError('This should NOT have happened!')

        agreement = self.create_pending_agreement(
            request=request,
            user=user,
            user_from=user_from,
            user_to=user_to,
        )

        session.add(agreement)
        session.flush()

        # Send e-mail to recipient of proposal
        if SEND_AGREEMENT_INVITATION_EMAIL:
            send_invitation_received_email(agreement)

        return SubmitAgreementProposalResponse(success=True)

    def create_pending_agreement(self, request, user, user_from, user_to):
        """
        :param SubmitAgreementProposalRequest request:
        :param User user:
        :param User user_from:
        :param User user_to:
        :rtype: TradeAgreement
        """
        agreement = TradeAgreement(
            user_proposed=user,
            user_from=user_from,
            user_to=user_to,
            state=AgreementState.PENDING,
            date_from=request.date.begin,
            date_to=request.date.end,
            reference=request.reference,
            amount=request.amount,
            unit=request.unit,
            amount_percent=request.amount_percent,
            technologies=request.technologies,
            limit_to_consumption=request.limit_to_consumption,
            proposal_note=request.proposal_note,
            facility_gsrn=request.facility_gsrn,
        )

        return agreement


class RespondToProposal(Controller):
    """
    TODO
    """
    Request = md.class_schema(RespondToProposalRequest)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param RespondToProposalRequest request:
        :param User user:
        :param Session session:
        :rtype: bool
        """
        agreement = AgreementQuery(session) \
            .has_public_id(request.public_id) \
            .is_awaiting_response_by(user) \
            .one_or_none()

        if not agreement:
            return False

        if request.accept:
            # Accept proposal
            self.accept_proposal(request, agreement, user, session)
        else:
            # Decline proposal
            self.decline_proposal(agreement, user)

        return True

    def accept_proposal(self, request, agreement, user, session):
        """
        :param RespondToProposalRequest request:
        :param TradeAgreement agreement:
        :param User user:
        :param Session session:
        """
        agreement.state = AgreementState.ACCEPTED
        agreement.transfer_priority = self.get_next_priority(
            agreement.user_from, session)

        if request.technologies and self.can_set_technology(agreement):
            agreement.technologies = request.technologies

        if request.facility_gsrn and self.can_set_facilities(agreement, user):
            agreement.facility_gsrn = request.facility_gsrn

        if request.amount_percent and self.can_set_amount_percent(agreement, user):
            agreement.amount_percent = request.amount_percent

        # Send e-mail to proposing user
        if SEND_AGREEMENT_INVITATION_EMAIL:
            send_invitation_accepted_email(agreement)

    def decline_proposal(self, agreement, user):
        """
        :param TradeAgreement agreement:
        :param User user:
        """
        agreement.decline_proposal()

        # Send e-mail to proposing user
        send_invitation_declined_email(agreement)

    def can_set_technology(self, agreement):
        """
        :param TradeAgreement agreement:
        :rtype: bool
        """
        return not agreement.technologies

    def can_set_facilities(self, agreement, user):
        """
        :param TradeAgreement agreement:
        :param User user:
        :rtype: bool
        """
        return agreement.is_outbound_from(user)

    def can_set_amount_percent(self, agreement, user):
        """
        :param User user:
        :param TradeAgreement agreement:
        :rtype: bool
        """
        return agreement.is_outbound_from(user)

    def get_next_priority(self, user, session):
        """
        :param User user:
        :param Session session:
        :rtype: int
        """
        current_max_priority = AgreementQuery(session) \
            .is_outbound_from(user) \
            .get_peiority_max()

        if current_max_priority is not None:
            return current_max_priority + 1
        else:
            return 0


class WithdrawProposal(Controller):
    """
    TODO
    """
    Request = md.class_schema(WithdrawProposalRequest)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param WithdrawProposalRequest request:
        :param User user:
        :param Session session:
        :rtype: bool
        """
        agreement = AgreementQuery(session) \
            .has_public_id(request.public_id) \
            .is_proposed_by(user) \
            .is_pending() \
            .one_or_none()

        if agreement:
            agreement.state = AgreementState.WITHDRAWN
            return True
        else:
            return False


class CountPendingProposals(Controller):
    """
    TODO
    """
    Response = md.class_schema(CountPendingProposalsResponse)

    @requires_login
    @inject_session
    def handle_request(self, user, session):
        """
        :param User user:
        :param Session session:
        :rtype: CountPendingProposalsResponse
        """
        count = AgreementQuery(session) \
            .is_awaiting_response_by(user) \
            .count()

        return CountPendingProposalsResponse(
            success=True,
            count=count,
        )
