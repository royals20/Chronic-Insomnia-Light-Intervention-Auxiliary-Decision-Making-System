from app.services.quality_service import build_data_quality_summary


def test_quality_summary_flags_invalid_and_incomplete_records(db_session):
    invalid_patient_id = db_session.info["patient_ids"]["invalid_patient_id"]
    incomplete_patient_id = db_session.info["patient_ids"]["incomplete_patient_id"]

    quality = build_data_quality_summary(db_session)
    blocking_codes = {item.issue_code for item in quality.blocking_issues}
    warning_codes = {item.issue_code for item in quality.warning_issues}

    assert quality.summary.total_patients >= 14
    assert quality.summary.blocking_issue_count > 0
    assert invalid_patient_id in quality.affected_patient_ids
    assert incomplete_patient_id in quality.affected_patient_ids
    assert "invalid_psqi_score" in blocking_codes
    assert "unparseable_followup_outcome" in blocking_codes
    assert "missing_baseline_feature" in blocking_codes
    assert "missing_followup_outcome" in blocking_codes
    assert "age_out_of_research_range" in warning_codes
    assert any(item.issue_code == "invalid_psqi_score" for item in quality.suggested_fixes)
