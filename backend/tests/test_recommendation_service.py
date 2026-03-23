from app.services.recommendation_service import (
    NOT_RECOMMEND_LEVEL,
    RECOMMEND_LEVEL,
    evaluate_patient,
)


def test_evaluate_patient_hits_recommendation_rules(db_session):
    patient_id = db_session.info["patient_ids"]["recommended_patient_id"]

    result = evaluate_patient(db_session, patient_id, save_result=False)

    assert result.saved is False
    assert result.recommendation_level == RECOMMEND_LEVEL
    assert result.benefit_score >= 72
    assert result.data_completeness_score >= 70
    assert any("失眠症状" in factor or "睡眠" in factor for factor in result.key_factors)


def test_evaluate_patient_falls_back_to_not_recommend_on_low_completeness(db_session):
    patient_id = db_session.info["patient_ids"]["incomplete_patient_id"]

    result = evaluate_patient(db_session, patient_id, save_result=False)

    assert result.saved is False
    assert result.recommendation_level == NOT_RECOMMEND_LEVEL
    assert result.data_completeness_score < 45
    assert any("缺少" in item for item in result.usage_limitations)
