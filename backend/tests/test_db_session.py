from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

import app.db.session as session_module
from app.models.user import User
from app.services.auth_service import authenticate_user


def test_init_db_migrates_legacy_users_table(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "legacy-users.db"
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER NOT NULL PRIMARY KEY,
                    username VARCHAR(64) NOT NULL,
                    password VARCHAR(128) NOT NULL,
                    full_name VARCHAR(128) NOT NULL
                )
                """
            )
        )
        connection.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username)"))
        connection.execute(text("CREATE INDEX ix_users_id ON users (id)"))
        connection.execute(
            text(
                """
                INSERT INTO users (id, username, password, full_name)
                VALUES (1, 'research_demo', 'Demo@123456', 'Research Demo')
                """
            )
        )

    monkeypatch.setattr(session_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(session_module.settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(session_module.settings, "model_artifact_dir", str(artifacts_dir))

    session_module.init_db()

    with engine.connect() as connection:
        columns = {
            row[1]: row
            for row in connection.execute(text("PRAGMA table_info(users)"))
        }
        assert columns["password"][3] == 0

    with TestingSessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "research_demo"))
        assert user is not None
        assert user.password is None
        assert user.password_hash
        assert authenticate_user(db, "research_demo", "Demo@123456") is not None

        admin_user = db.scalar(select(User).where(User.username == session_module.settings.admin_demo_username))
        assert admin_user is not None

    engine.dispose()
