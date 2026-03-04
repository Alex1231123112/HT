from admin.api.services import analytics_csv, logs_csv, users_csv
from database.models import User, UserType


def test_csv_builders():
    users = [User(id=1, username="u", user_type=UserType.HORECA, establishment="E")]
    ucsv = users_csv(users)
    lcsv = logs_csv([{"id": 1, "admin_id": 1, "action": "a", "details": "d", "created_at": "2026-01-01"}])
    acsv = analytics_csv({"users_total": 10})
    assert "users_total,10" in acsv
    assert "id,admin_id,action,details,created_at" in lcsv
    assert "id,username," in ucsv and "user_type,establishment," in ucsv and "phone_number" in ucsv and "full_name" in ucsv
