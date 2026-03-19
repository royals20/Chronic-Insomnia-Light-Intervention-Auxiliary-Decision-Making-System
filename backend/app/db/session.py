from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
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
            connection.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")
            )


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

    settings.model_artifact_path.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        demo_user = db.scalar(select(User).where(User.username == settings.demo_username))
        if demo_user is None:
            db.add(
                User(
                    username=settings.demo_username,
                    password=settings.demo_password,
                    full_name=settings.demo_full_name,
                )
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
                "description": "用于科研辅助演示的规则/评分版推荐引擎。",
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
