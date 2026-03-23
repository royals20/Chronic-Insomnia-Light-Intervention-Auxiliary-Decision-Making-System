from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.auth import router as auth_router
from app.api.routes.data_imports import router as data_import_router
from app.api.routes.model_center import router as model_center_router
from app.api.routes.patients import router as patient_router
from app.api.routes.quality import router as quality_router
from app.api.routes.recommendations import router as recommendation_router
from app.api.routes.reports import router as report_router
from app.api.routes.system_settings import router as system_settings_router
from app.api.routes.users import router as users_router
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.models.baseline_feature import BaselineFeature
from app.models.followup_outcome import FollowupOutcome
from app.models.light_intervention import LightIntervention
from app.models.patient import Patient
from app.models.questionnaire_score import QuestionnaireScore
from app.models.sleep_metric import SleepMetric
from app.models.user import User
from app.services import model_center_service


def _build_valid_patient(index: int) -> Patient:
    enhanced = index % 2 == 0
    patient = Patient(
        patient_code=f"P{index:03d}",
        anonymized_code=f"A{index:03d}",
        gender="male" if index % 3 == 0 else "female",
        age=26 + index,
        height_cm=160 + (index % 5) * 2,
        weight_kg=54 + index,
        education_level=["high_school", "college", "master"][index % 3],
        remarks="test sample",
    )
    patient.baseline_feature = BaselineFeature(
        work_rest_schedule="late_sleep_late_rise",
        disease_duration=f"{6 + index} months",
        medication_usage="occasional_sleep_aid" if index % 4 else "no_medication",
        comorbidities="none",
        psychological_status="mild_anxiety" if index % 3 else "anxiety_combined",
        sleep_habits="difficulty_falling_asleep",
        notes="",
    )
    patient.questionnaire_score = QuestionnaireScore(
        psqi_score=10 + index % 4,
        isi_score=15 + index % 5,
        anxiety_score=8 + index % 4,
        depression_score=6 + index % 5,
        assessed_at=date(2026, 1, (index % 20) + 1),
    )
    patient.sleep_metric = SleepMetric(
        total_sleep_time_hours=5.2 + (index % 3) * 0.4,
        sleep_latency_minutes=28 + (index % 4) * 5,
        sleep_efficiency=72 + index % 8,
        awakening_count=2 + index % 3,
        notes="",
    )
    patient.light_intervention = LightIntervention(
        intensity_lux=3600 if enhanced else 2200,
        start_period="morning",
        duration_minutes=45 if enhanced else 30,
        intervention_days=14 if enhanced else 10,
        adherence="high" if enhanced else "medium",
        adverse_events="none",
    )
    patient.followup_outcome = FollowupOutcome(
        followup_date=date(2026, 2, (index % 20) + 1),
        primary_outcome=f"ISI improvement {4 + index % 5}",
        secondary_outcome=f"PSQI improvement {2 + index % 3}",
        notes="",
    )
    return patient


def _seed_test_data(session) -> dict[str, int]:
    session.add_all(
        [
            User(
                username="admin_demo",
                full_name="System Admin",
                role="admin",
                is_active=True,
                password_hash=hash_password("Admin@123456"),
            ),
            User(
                username="research_demo",
                full_name="Research Demo",
                role="researcher",
                is_active=True,
                password_hash=hash_password("Demo@123456"),
            ),
            User(
                username="data_entry_demo",
                full_name="Data Entry Demo",
                role="data_entry",
                is_active=True,
                password_hash=hash_password("Entry@123456"),
            ),
            User(
                username="disabled_demo",
                full_name="Disabled Demo",
                role="researcher",
                is_active=False,
                password_hash=hash_password("Disabled@123456"),
            ),
        ]
    )

    valid_patients = [_build_valid_patient(index) for index in range(1, 13)]
    session.add_all(valid_patients)

    invalid_patient = Patient(
        patient_code="P900",
        anonymized_code="A900",
        gender="female",
        age=86,
        height_cm=162,
        weight_kg=58,
        education_level="college",
        remarks="contains abnormal values",
    )
    invalid_patient.baseline_feature = BaselineFeature(
        work_rest_schedule="irregular",
        disease_duration="3 years",
        medication_usage="regular_sleep_aid",
        comorbidities="none",
        psychological_status="anxiety_combined",
        sleep_habits="frequent_awakening",
        notes="",
    )
    invalid_patient.questionnaire_score = QuestionnaireScore(
        psqi_score=25,
        isi_score=18,
        anxiety_score=26,
        depression_score=30,
        assessed_at=None,
    )
    invalid_patient.sleep_metric = SleepMetric(
        total_sleep_time_hours=26,
        sleep_latency_minutes=700,
        sleep_efficiency=120,
        awakening_count=25,
        notes="",
    )
    invalid_patient.light_intervention = LightIntervention(
        intensity_lux=12000,
        start_period="morning",
        duration_minutes=240,
        intervention_days=400,
        adherence="low",
        adverse_events="headache",
    )
    invalid_patient.followup_outcome = FollowupOutcome(
        followup_date=date(2026, 2, 21),
        primary_outcome="marked improvement",
        secondary_outcome=None,
        notes="",
    )
    session.add(invalid_patient)

    incomplete_patient = Patient(
        patient_code="P901",
        anonymized_code="A901",
        gender="male",
        age=42,
        height_cm=175,
        weight_kg=73,
        education_level="master",
        remarks="missing several sections",
    )
    session.add(incomplete_patient)

    session.commit()

    return {
        "recommended_patient_id": valid_patients[1].id,
        "incomplete_patient_id": incomplete_patient.id,
        "invalid_patient_id": invalid_patient.id,
    }


@pytest.fixture()
def db_session(tmp_path: Path, monkeypatch):
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(model_center_service, "BACKEND_ROOT", tmp_path)
    monkeypatch.setattr(model_center_service.settings, "model_artifact_dir", str(artifacts_dir))

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    session.info["patient_ids"] = _seed_test_data(session)

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def api_client(db_session):
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(patient_router, prefix="/api/v1")
    app.include_router(data_import_router, prefix="/api/v1")
    app.include_router(recommendation_router, prefix="/api/v1")
    app.include_router(report_router, prefix="/api/v1")
    app.include_router(quality_router, prefix="/api/v1")
    app.include_router(system_settings_router, prefix="/api/v1")
    app.include_router(model_center_router, prefix="/api/v1")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client


@pytest.fixture()
def auth_headers(api_client):
    def build(username: str, password: str) -> dict[str, str]:
        response = api_client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return build
