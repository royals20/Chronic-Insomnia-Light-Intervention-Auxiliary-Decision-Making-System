from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.models import ModelVersion, User

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _ensure_pending_tables() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    pending_tables = [
        table for table in Base.metadata.sorted_tables if table.name not in existing_tables
    ]
    if pending_tables:
        Base.metadata.create_all(bind=engine, tables=pending_tables)


def _add_missing_columns(table_name: str, columns: dict[str, str]) -> None:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    with engine.begin() as connection:
        for column_name, column_sql in columns.items():
            if column_name in existing_columns:
                continue
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


def _get_table_columns(table_name: str) -> dict[str, dict]:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return {}
    return {column["name"]: column for column in inspector.get_columns(table_name)}


def _rebuild_sqlite_users_table_if_needed() -> None:
    columns = _get_table_columns("users")
    password_column = columns.get("password")
    if password_column is None or password_column.get("nullable", True):
        return

    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=OFF"))
        connection.execute(text("DROP TABLE IF EXISTS users__migration"))
        connection.execute(
            text(
                """
                CREATE TABLE users__migration (
                    id INTEGER NOT NULL PRIMARY KEY,
                    username VARCHAR(64) NOT NULL,
                    password VARCHAR(128),
                    password_hash VARCHAR(255),
                    full_name VARCHAR(128) NOT NULL,
                    role VARCHAR(32) NOT NULL DEFAULT 'researcher',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    last_login_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO users__migration (
                    id,
                    username,
                    password,
                    password_hash,
                    full_name,
                    role,
                    is_active,
                    last_login_at,
                    created_at,
                    updated_at
                )
                SELECT
                    id,
                    username,
                    password,
                    password_hash,
                    full_name,
                    COALESCE(NULLIF(role, ''), 'researcher'),
                    COALESCE(is_active, 1),
                    last_login_at,
                    COALESCE(created_at, CURRENT_TIMESTAMP),
                    COALESCE(updated_at, CURRENT_TIMESTAMP)
                FROM users
                """
            )
        )
        connection.execute(text("DROP TABLE users"))
        connection.execute(text("ALTER TABLE users__migration RENAME TO users"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)"))
        connection.execute(text("PRAGMA foreign_keys=ON"))


def _ensure_demo_user(
    db,
    *,
    username: str,
    password: str,
    full_name: str,
    role: str,
) -> None:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        db.add(
            User(
                username=username,
                full_name=full_name,
                role=role,
                is_active=True,
                password_hash=hash_password(password),
                password=None,
            )
        )
        return

    user.full_name = user.full_name or full_name
    user.role = user.role or role
    if user.is_active is None:
        user.is_active = True
    if not user.password_hash:
        legacy_password = user.password or password
        user.password_hash = hash_password(legacy_password)
    user.password = None
    user.updated_at = datetime.utcnow()


def _migrate_legacy_users(db) -> None:
    for user in db.scalars(select(User)).all():
        changed = False
        if not user.role:
            user.role = "researcher"
            changed = True
        if user.is_active is None:
            user.is_active = True
            changed = True
        if not user.password_hash and user.password:
            user.password_hash = hash_password(user.password)
            changed = True
        if user.created_at is None:
            user.created_at = datetime.utcnow()
            changed = True
        if user.updated_at is None:
            user.updated_at = datetime.utcnow()
            changed = True
        if changed:
            user.password = None


def init_db() -> None:
    _ensure_pending_tables()

    if settings.database_url.startswith("sqlite"):
        _add_missing_columns(
            "prediction_results",
            {
                "data_completeness_score": "FLOAT",
                "key_factors_text": "TEXT",
                "limitations_text": "TEXT",
                "engine_name": "VARCHAR(128)",
                "engine_version": "VARCHAR(64)",
                "rule_snapshot_text": "TEXT",
            },
        )
        _add_missing_columns(
            "model_versions",
            {
                "artifact_path": "VARCHAR(255)",
                "metrics_text": "TEXT",
                "config_text": "TEXT",
                "feature_list_text": "TEXT",
                "training_started_at": "DATETIME",
                "training_completed_at": "DATETIME",
            },
        )
        _add_missing_columns(
            "users",
            {
                "password_hash": "VARCHAR(255)",
                "role": "VARCHAR(32) DEFAULT 'researcher'",
                "is_active": "BOOLEAN DEFAULT 1",
                "last_login_at": "DATETIME",
                "created_at": "DATETIME",
                "updated_at": "DATETIME",
            },
        )
        _rebuild_sqlite_users_table_if_needed()

    settings.model_artifact_path.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        _migrate_legacy_users(db)
        _ensure_demo_user(
            db,
            username=settings.admin_demo_username,
            password=settings.admin_demo_password,
            full_name=settings.admin_demo_full_name,
            role="admin",
        )
        _ensure_demo_user(
            db,
            username=settings.demo_username,
            password=settings.demo_password,
            full_name=settings.demo_full_name,
            role="researcher",
        )
        _ensure_demo_user(
            db,
            username=settings.data_entry_demo_username,
            password=settings.data_entry_demo_password,
            full_name=settings.data_entry_demo_full_name,
            role="data_entry",
        )

        default_model_versions = [
            {
                "name": "规则基线版",
                "version_type": "rule",
                "status": "active",
                "description": "用于科研原型演示的规则推荐版本。",
            },
            {
                "name": "预测模型试验版",
                "version_type": "predictive",
                "status": "inactive",
                "description": "用于后续接入监督学习模型的占位版本。",
            },
            {
                "name": "因果推断试验版",
                "version_type": "causal",
                "status": "inactive",
                "description": "用于后续接入因果效应估计模型的占位版本。",
            },
            {
                "name": "规则评分引擎V1",
                "version_type": "rule",
                "status": "active",
                "description": "用于科研辅助演示的规则评分版推荐引擎。",
            },
        ]

        for payload in default_model_versions:
            existing = db.scalar(select(ModelVersion).where(ModelVersion.name == payload["name"]))
            if existing is None:
                db.add(ModelVersion(**payload))

        db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
