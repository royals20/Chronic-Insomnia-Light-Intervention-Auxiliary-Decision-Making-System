from app.models.audit_log import AuditLog


def add_audit_log(
    db,
    *,
    actor_name: str,
    action_type: str,
    target_type: str,
    target_id: str | None = None,
    details: dict | None = None,
    detail_text: str | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_name=actor_name,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        details=details,
        detail_text=detail_text,
    )
    db.add(audit_log)
    return audit_log
