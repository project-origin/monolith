# import originexample.services.account as acc
from origin.common import SummaryResolution


def get_resolution(delta):
    """
    TODO write me

    :param timedelta delta:
    :rtype: SummaryResolution
    """
    if delta.days >= (365 * 3):
        return SummaryResolution.year
    elif delta.days >= 60:
        return SummaryResolution.month
    elif delta.days >= 3:
        return SummaryResolution.day
    else:
        return SummaryResolution.hour


def update_transfer_priorities(user, session):
    """
    TODO write me

    :param User user:
    :param sqlalchemy.orm.Session session:
    """
    session.execute("""
        update agreements_agreement
        set transfer_priority = s.row_number - 1
        from (
            select a.id, row_number() over (
                partition by a.user_from_subject
                order by a.transfer_priority asc
            )
          from agreements_agreement as a
          where a.state = 'ACCEPTED'
          order by a.transfer_priority asc
        ) as s
        where agreements_agreement.id = s.id
        and agreements_agreement.user_from_subject = :user_from_subject
    """, {'user_from_subject': user.subject})
