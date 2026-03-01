from admin.api.services import analytics_csv, logs_csv, matches_target, users_csv
from database.models import Mailing, MailingTarget, User, UserType


def test_matches_target_all():
    user = User(id=1, user_type=UserType.HORECA, establishment="A")
    mailing = Mailing(text="x", target_type=MailingTarget.ALL)
    assert matches_target(user, mailing) is True


def test_matches_target_custom():
    user = User(id=7, user_type=UserType.RETAIL, establishment="A")
    mailing = Mailing(text="x", target_type=MailingTarget.CUSTOM, custom_targets=[7, 8])
    assert matches_target(user, mailing) is True


def test_csv_builders():
    users = [User(id=1, username="u", user_type=UserType.HORECA, establishment="E")]
    ucsv = users_csv(users)
    lcsv = logs_csv([{"id": 1, "admin_id": 1, "action": "a", "details": "d", "created_at": "2026-01-01"}])
    acsv = analytics_csv({"users_total": 10})
    assert "users_total,10" in acsv
    assert "id,admin_id,action,details,created_at" in lcsv
    assert "id,username," in ucsv and "user_type,establishment," in ucsv and "phone_number" in ucsv and "full_name" in ucsv
