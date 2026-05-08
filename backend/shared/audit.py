import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from .models import AuditEvent

async def record_audit(
    db: AsyncSession,
    event_type: str,        # "create", "update", "delete", "validate", "reject", "homologate"
    entity_type: str,       # "invoice", "invoice_line", "material", "provider", "user", "document"
    entity_id: int,
    user_id: int | None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    notes: str | None = None,
) -> None:
    """Fire-and-forget audit log. Swallows exceptions so it never breaks the main flow."""
    try:
        event = AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            notes=notes,
        )
        db.add(event)
        # Don't flush here — let the caller's transaction commit it
    except Exception:
        pass
