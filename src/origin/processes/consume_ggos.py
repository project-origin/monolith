from math import floor
from itertools import takewhile

from origin.auth import User
from origin.measurements import MeasurementQuery
from origin.meteringpoints import MeteringPoint, MeteringPointQuery
from origin.agreements import TradeAgreement, AgreementQuery

from origin.ggo import GgoComposer, GgoQuery, TransactionQuery


def handle_ggo_received(ggo, session):
    """
    Invoked whenever a user receives a new GGO.
    This effectuates retire and/or transferring via agreements.

    :param origin.ggo.Ggo ggo:
    :param sqlalchemy.orm.Session session:
    """
    if not ggo.stored:
        return

    controller = GgoConsumerController()
    controller.consume_ggo(ggo.user, ggo, session)


class GgoConsumerController(object):
    """
    TODO
    """

    def get_consumers(self, user, ggo, session):
        """
        :param origin.auth.User user:
        :param origin.ggo.Ggo ggo:
        :param sqlalchemy.orm.Session session:
        :rtype: collections.abc.Iterable[GgoConsumer]
        """
        yield from self.get_retire_consumers(user, ggo, session)
        yield from self.get_agreement_consumers(user, ggo, session)

    def get_retire_consumers(self, user, ggo, session):
        """
        TODO test this

        :param User user:
        :param Ggo ggo:
        :param sqlalchemy.orm.Session session:
        :rtype: collections.abc.Iterable[RetiringConsumer]
        """
        facilities = MeteringPointQuery(session) \
            .belongs_to(user) \
            .is_retire_receiver() \
            .is_eligible_to_retire(ggo) \
            .order_by(MeteringPoint.retiring_priority.asc()) \
            .all()

        for facility in facilities:
            yield RetiringConsumer(facility, session)

    def get_agreement_consumers(self, user, ggo, session):
        """
        TODO test this

        :param User user:
        :param Ggo ggo:
        :param sqlalchemy.orm.Session session:
        :rtype: collections.abc.Iterable[AgreementConsumer]
        """
        agreements = AgreementQuery(session) \
            .is_outbound_from(user) \
            .is_elibigle_to_trade(ggo) \
            .is_operating_at(ggo.begin) \
            .is_active() \
            .order_by(TradeAgreement.transfer_priority.asc()) \
            .all()

        # TODO test query ordering (transfer_priority)

        for agreement in agreements:
            if agreement.limit_to_consumption:
                yield AgreementLimitedToConsumptionConsumer(agreement, session)
            else:
                yield AgreementConsumer(agreement, session)

    def consume_ggo(self, user, ggo, session):
        """
        :param User user:
        :param Ggo ggo:
        :param Session session:
        """
        composer = GgoComposer(ggo, session)
        consumers = self.get_consumers(user, ggo, session)
        remaining_amount = ggo.amount

        for consumer in takewhile(lambda _: remaining_amount > 0, consumers):
            already_transferred = ggo.amount - remaining_amount

            desired_amount = consumer.get_desired_amount(
                ggo, already_transferred)

            assigned_amount = min(remaining_amount, desired_amount)
            remaining_amount -= assigned_amount

            if assigned_amount > 0:
                consumer.consume(composer, ggo, assigned_amount)

        if remaining_amount < ggo.amount:
            batch, recipients = composer.build_batch()
            batch.on_commit()

            session.add(batch)

    def get_affected_subjects(self, user, ggo, session):
        """
        :param User user:
        :param Ggo ggo:
        :param Session session:
        :rtype: list[str]
        """
        unique_subjects = set([user.sub])

        for consumer in self.get_consumers(user, ggo, session):
            unique_subjects.update(consumer.get_affected_subjects())

        return list(unique_subjects)


class GgoConsumer(object):
    """
    TODO
    """
    def get_affected_subjects(self):
        """
        :rtype: list[str]
        """
        raise NotImplementedError

    def consume(self, composer, ggo, amount):
        """
        :param GgoComposer composer:
        :param Ggo ggo:
        :param int amount:
        """
        raise NotImplementedError

    def get_desired_amount(self, ggo, already_transferred):
        """
        :param Ggo ggo:
        :param int already_transferred:
        :rtype: int
        """
        raise NotImplementedError


class RetiringConsumer(GgoConsumer):
    """
    TODO
    """
    def __init__(self, meteringpoint, session):
        """
        :param MeteringPoint meteringpoint:
        :param sqlalchemy.orm.Session session:
        """
        self.meteringpoint = meteringpoint
        self.session = session

    def __str__(self):
        return 'RetiringConsumer<%s>' % self.meteringpoint.gsrn

    def get_affected_subjects(self):
        """
        :rtype: list[str]
        """
        return [self.meteringpoint.subject]

    def consume(self, composer, ggo, amount):
        """
        :param GgoComposer composer:
        :param Ggo ggo:
        :param int amount:
        """
        composer.add_retire(
            meteringpoint=self.meteringpoint,
            amount=amount,
        )

    def get_desired_amount(self, ggo, already_transferred):
        """
        :param Ggo ggo:
        :param int already_transferred:
        :rtype: int
        """
        measurement = get_consumption(
            user=self.meteringpoint.user,
            gsrn=self.meteringpoint.gsrn,
            begin=ggo.begin,
            session=self.session,
        )

        if measurement is None:
            return 0

        retired_amount = get_retired_amount(
            user=self.meteringpoint.user,
            gsrn=self.meteringpoint.gsrn,
            measurement=measurement,
            session=self.session,
        )

        desired_amount = measurement.amount - retired_amount

        return max(0, min(ggo.amount, desired_amount))


class AgreementConsumer(GgoConsumer):
    """
    TODO
    """
    def __init__(self, agreement, session):
        """
        :param TradeAgreement agreement:
        :param sqlalchemy.orm.Session session:
        """
        self.agreement = agreement
        self.reference = agreement.public_id
        self.session = session

    def __str__(self):
        return 'AgreementConsumer<%s>' % self.reference

    def get_affected_subjects(self):
        """
        :rtype: list[str]
        """
        return [self.agreement.user_to.sub]

    def consume(self, composer, ggo, amount):
        """
        :param GgoComposer composer:
        :param Ggo ggo:
        :param int amount:
        """
        composer.add_transfer(
            user=self.agreement.user_to,
            amount=amount,
            reference=self.reference,
        )

    def get_desired_amount(self, ggo, already_transferred):
        """
        :param Ggo ggo:
        :param int already_transferred:
        :rtype: int
        """
        transferred_amount = get_transferred_amount(
            user=self.agreement.user_from,
            reference=self.reference,
            begin=ggo.begin,
            session=self.session,
        )

        if self.agreement.amount_percent:
            # Transfer percentage of ggo.amount
            percentage_amount = self.agreement.amount_percent / 100 * ggo.amount
            desired_amount = min(self.agreement.calculated_amount,
                                 floor(percentage_amount))
            desired_amount = desired_amount - transferred_amount
        else:
            # Transfer all of ggo.amount
            desired_amount = self.agreement.calculated_amount - transferred_amount

        return max(0, min(ggo.amount, desired_amount))


class AgreementLimitedToConsumptionConsumer(AgreementConsumer):
    """
    TODO
    """
    def __init__(self, agreement, session):
        """
        :param TradeAgreement agreement:
        :param sqlalchemy.orm.Session session:
        """
        super(AgreementLimitedToConsumptionConsumer, self).__init__(agreement)
        self.session = session

    def __str__(self):
        return 'AgreementLimitedToConsumptionConsumer<%s>' % self.reference

    def get_affected_subjects(self):
        """
        :rtype: list[str]
        """
        return [
            self.agreement.user_from_subject,
            self.agreement.user_to_subject,
        ]

    def get_desired_amount(self, ggo, already_transferred):
        """
        :param Ggo ggo:
        :param int already_transferred:
        :rtype: int
        """
        remaining_amount = super(AgreementLimitedToConsumptionConsumer, self) \
            .get_desired_amount(ggo, already_transferred)

        if remaining_amount <= 0:
            return 0

        desired_amount = 0

        # TODO takewhile desired_amount < min(ggo.amount, remaining_amount)
        for facility in self.get_facilities(ggo):
            desired_amount += self.get_desired_amount_for_facility(
                facility=facility,
                begin=ggo.begin,
            )

        desired_amount -= already_transferred
        try:
            desired_amount -= get_stored_amount(
                user=self.agreement.user_to,
                begin=ggo.begin,
                session=self.session,
            )
        except Exception as e:
            raise

        return max(0, min(ggo.amount, remaining_amount, desired_amount))

    def get_desired_amount_for_facility(self, facility, begin):
        """
        :param Facility facility:
        :param datetime.datetime begin:
        :rtype: int
        """
        try:
            measurement = get_consumption(
                user=self.agreement.user_to,
                gsrn=facility.gsrn,
                begin=begin,
                session=self.session,
            )
        except Exception as e:
            raise

        if measurement is None:
            return 0

        retired_amount = get_retired_amount(
            user=self.agreement.user_to,
            gsrn=facility.gsrn,
            measurement=measurement,
            session=self.session,
        )

        remaining_amount = measurement.amount - retired_amount

        return max(0, remaining_amount)

    def get_facilities(self, ggo):
        """
        :param Ggo ggo:
        :rtype: list[Facility]
        """
        return MeteringPointQuery(self.session) \
            .belongs_to(self.agreement.user_to) \
            .is_retire_receiver() \
            .is_eligible_to_retire(ggo) \
            .all()


# -- Helpers -----------------------------------------------------------------


def get_consumption(user, gsrn, begin, session):
    """
    :param str gsrn:
    :param datetime.datetime begin:
    :param sqlalchemy.orm.Session session:
    :rtype: Measurement
    """
    return MeasurementQuery(session) \
        .belongs_to(user) \
        .has_gsrn(gsrn) \
        .begins_at(begin) \
        .one_or_none()

    # request = GetMeasurementRequest(gsrn=gsrn, begin=begin)
    # response = datahub_service.get_consumption(token, request)
    # return response.measurement


def get_stored_amount(user, begin, session):
    """
    :param origin.auth.User user:
    :param datetime.datetime begin:
    :param sqlalchemy.orm.Session session:
    :rtype: int
    """
    return GgoQuery(session) \
        .belongs_to(user) \
        .begins_at(begin) \
        .is_stored() \
        .get_total_amount()

    # request = GetTotalAmountRequest(
    #     filters=GgoFilters(
    #         begin=begin,
    #         category=GgoCategory.STORED,
    #     )
    # )
    # response = account_service.get_total_amount(token, request)
    # return response.amount


def get_retired_amount(user, gsrn, measurement, session):
    """
    :param origin.auth.User user:
    :param str gsrn:
    :param Measurement measurement:
    :param sqlalchemy.orm.Session session:
    :rtype: int
    """
    return GgoQuery(session) \
        .belongs_to(user) \
        .is_retired() \
        .is_retired_to_gsrn(gsrn) \
        .is_retired_to_measurement(measurement) \
        .get_total_amount()

    # request = GetTotalAmountRequest(
    #     filters=GgoFilters(
    #         retire_gsrn=[gsrn],
    #         retire_address=[measurement.address],
    #         category=GgoCategory.RETIRED,
    #     )
    # )
    # response = account_service.get_total_amount(token, request)
    # return response.amount


def get_transferred_amount(user, reference, begin, session):
    """
    :param origin.auth.User user:
    :param str reference:
    :param datetime.datetime begin:
    :param sqlalchemy.orm.Session session:
    :rtype: int
    """
    return TransactionQuery(session) \
        .sent_by_user(user) \
        .begins_at(begin) \
        .has_reference(reference) \
        .get_total_amount()

    # request = GetTransferredAmountRequest(
    #     direction=TransferDirection.OUTBOUND,
    #     filters=TransferFilters(
    #         reference=[reference],
    #         begin=begin,
    #     )
    # )
    # response = account_service.get_transferred_amount(token, request)
    # return response.amount


# def ggo_is_available(ggo):
#     """
#     Check whether a GGO is available for transferring/retiring.
#
#     :param Ggo ggo:
#     :rtype: bool
#     """
#     request = GetGgoListRequest(
#         filters=GgoFilters(
#             address=[ggo.address],
#             category=GgoCategory.STORED,
#         )
#     )
#     response = account_service.get_ggo_list(token, request)
#     return len(response.results) > 0
