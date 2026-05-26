"""Тесты защиты от зацикленной рассылки контент-плана."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from admin.api.content_plan_sender import process_due_content_plans, try_claim_content_plan
from database.models import ContentPlan, ContentPlanStatus
from database.session import SessionLocal

pytestmark = pytest.mark.asyncio


async def _create_scheduled_plan(title: str = "Loop test") -> ContentPlan:
    async with SessionLocal() as db:
        plan = ContentPlan(
            title=title,
            content_type="custom",
            custom_title="Test",
            custom_description="Body",
            scheduled_at=datetime.utcnow() - timedelta(minutes=1),
            status=ContentPlanStatus.SCHEDULED,
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan


async def test_try_claim_content_plan_marks_sent_before_send():
    plan = await _create_scheduled_plan("claim test")
    async with SessionLocal() as db:
        plan_row = await db.get(ContentPlan, plan.id)
        claimed = await try_claim_content_plan(db, plan_row)
        assert claimed is True
        assert plan_row.status == ContentPlanStatus.SENT
        assert plan_row.sent_at is not None

    async with SessionLocal() as db:
        again = await db.get(ContentPlan, plan.id)
        claimed_again = await try_claim_content_plan(db, again)
        assert claimed_again is False


async def test_process_due_does_not_resend_after_claim():
    plan = await _create_scheduled_plan("no loop")
    send_mock = AsyncMock(return_value={"sent_bot": 1, "sent_channel": 0, "errors": [], "channels_count": 1})

    with patch("admin.api.content_plan_sender.send_plan_to_telegram", send_mock):
        async with SessionLocal() as db:
            processed = await process_due_content_plans(db, "test-token")
            assert processed >= 1

        async with SessionLocal() as db:
            processed_again = await process_due_content_plans(db, "test-token")
            assert processed_again == 0

    assert send_mock.call_count == 1
