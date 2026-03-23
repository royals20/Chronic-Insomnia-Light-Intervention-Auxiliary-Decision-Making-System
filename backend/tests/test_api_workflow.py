from app.modeling.estimators import FallbackNearestNeighborCausalEstimator
from app.services import model_center_service
from app.services.import_service import generate_template_file


def test_login_success_and_failure(api_client):
    success = api_client.post(
        "/api/v1/auth/login",
        json={"username": "research_demo", "password": "Demo@123456"},
    )
    assert success.status_code == 200
    payload = success.json()
    assert payload["user"]["username"] == "research_demo"
    assert payload["user"]["role"] == "researcher"
    assert payload["expires_in"] > 0

    failure = api_client.post(
        "/api/v1/auth/login",
        json={"username": "research_demo", "password": "wrong-password"},
    )
    assert failure.status_code == 401

    disabled = api_client.post(
        "/api/v1/auth/login",
        json={"username": "disabled_demo", "password": "Disabled@123456"},
    )
    assert disabled.status_code == 403


def test_protected_route_requires_token(api_client):
    response = api_client.get("/api/v1/quality/summary")

    assert response.status_code == 401


def test_data_entry_permissions(api_client, auth_headers):
    headers = auth_headers("data_entry_demo", "Entry@123456")

    quality_response = api_client.get("/api/v1/quality/summary", headers=headers)
    assert quality_response.status_code == 200
    assert "summary" in quality_response.json()

    create_response = api_client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "patient_code": "NEW-001",
            "anonymized_code": "ANON-NEW-001",
            "gender": "female",
            "age": 30,
            "height_cm": 165,
            "weight_kg": 55,
            "education_level": "master",
            "remarks": "data entry create",
        },
    )
    assert create_response.status_code == 201

    template_bytes, _, _ = generate_template_file("csv")
    import_response = api_client.post(
        "/api/v1/imports/patients",
        headers=headers,
        files={"file": ("patients.csv", template_bytes, "text/csv")},
    )
    assert import_response.status_code == 200
    assert import_response.json()["summary"]["success_count"] >= 1

    delete_response = api_client.delete("/api/v1/patients/1", headers=headers)
    assert delete_response.status_code == 403

    settings_response = api_client.get("/api/v1/system-settings/recommendation-rules", headers=headers)
    assert settings_response.status_code == 403

    train_response = api_client.post(
        "/api/v1/model-center/train",
        headers=headers,
        json={
            "model_name": "data-entry-train-check",
            "test_ratio": 0.2,
            "random_seed": 20260319,
            "max_features": 8,
            "min_feature_coverage": 0.7,
            "activate_after_train": True,
        },
    )
    assert train_response.status_code == 403


def test_researcher_can_train_but_cannot_import(api_client, auth_headers, monkeypatch):
    headers = auth_headers("research_demo", "Demo@123456")
    monkeypatch.setattr(
        model_center_service,
        "build_causal_estimator",
        lambda: FallbackNearestNeighborCausalEstimator(),
    )

    create_response = api_client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "patient_code": "NEW-002",
            "anonymized_code": "ANON-NEW-002",
            "gender": "male",
            "age": 31,
            "height_cm": 170,
            "weight_kg": 65,
            "education_level": "college",
            "remarks": "researcher write check",
        },
    )
    assert create_response.status_code == 403

    template_bytes, _, _ = generate_template_file("csv")
    import_response = api_client.post(
        "/api/v1/imports/patients",
        headers=headers,
        files={"file": ("patients.csv", template_bytes, "text/csv")},
    )
    assert import_response.status_code == 403

    train_response = api_client.post(
        "/api/v1/model-center/train",
        headers=headers,
        json={
            "model_name": "reproducibility-check",
            "test_ratio": 0.2,
            "random_seed": 20260319,
            "max_features": 8,
            "min_feature_coverage": 0.7,
            "activate_after_train": True,
        },
    )
    assert train_response.status_code == 200
    train_payload = train_response.json()
    version_id = train_payload["model_version"]["id"]
    assert train_payload["result"]["engine_backend"] == "fallback_nearest_neighbor"
    assert train_payload["model_version"]["selected_feature_keys"]

    activate_response = api_client.post(
        f"/api/v1/model-center/versions/{version_id}/activate",
        headers=headers,
    )
    assert activate_response.status_code == 200
    assert activate_response.json()["status"] == "active"


def test_admin_user_management_flow(api_client, auth_headers):
    headers = auth_headers("admin_demo", "Admin@123456")

    list_response = api_client.get("/api/v1/users", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 3

    create_response = api_client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "new_researcher",
            "full_name": "New Researcher",
            "role": "researcher",
            "password": "NewDemo@123456",
            "is_active": True,
        },
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    update_response = api_client.put(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"full_name": "Updated Researcher", "role": "data_entry", "is_active": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["role"] == "data_entry"

    reset_response = api_client.post(
        f"/api/v1/users/{user_id}/reset-password",
        headers=headers,
        json={"new_password": "Reset@123456"},
    )
    assert reset_response.status_code == 200

    toggle_response = api_client.post(f"/api/v1/users/{user_id}/toggle-active", headers=headers)
    assert toggle_response.status_code == 200
    assert toggle_response.json()["is_active"] is False
