"""Audit logger - writes to audit_log table."""

import structlog
from datetime import datetime, timezone

logger = structlog.get_logger()


class AuditLogger:
    """Writes audit log entries."""

    def __init__(self, db):
        self.db = db

    async def log(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            entity_type: Type of entity (e.g., "account", "device")
            entity_id: ID of the entity
            action: Action taken (e.g., "status_change", "job_created")
            actor: Who performed the action
            old_value: Previous state (for changes)
            new_value: New state (for changes)
            metadata: Additional context
        """
        # TODO: Implement - insert into audit_log table
        logger.info(
            "audit_log",
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
        )
