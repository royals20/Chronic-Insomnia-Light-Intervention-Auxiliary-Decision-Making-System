import apiClient from '@/api/client';

export interface PatientListItem {
  id: number;
  patient_code: string;
  anonymized_code: string;
  gender: string | null;
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  education_level: string | null;
  remarks: string | null;
  created_at: string;
  updated_at: string;
  has_baseline_feature: boolean;
  has_questionnaire_score: boolean;
  has_sleep_metric: boolean;
  has_light_intervention: boolean;
  has_followup_outcome: boolean;
}

export interface BaselineFeature {
  id?: number;
  work_rest_schedule: string | null;
  disease_duration: string | null;
  medication_usage: string | null;
  comorbidities: string | null;
  psychological_status: string | null;
  sleep_habits: string | null;
  notes: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface QuestionnaireScore {
  id?: number;
  psqi_score: number | null;
  isi_score: number | null;
  anxiety_score: number | null;
  depression_score: number | null;
  assessed_at: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface SleepMetric {
  id?: number;
  total_sleep_time_hours: number | null;
  sleep_latency_minutes: number | null;
  sleep_efficiency: number | null;
  awakening_count: number | null;
  notes: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface LightIntervention {
  id?: number;
  intensity_lux: number | null;
  start_period: string | null;
  duration_minutes: number | null;
  intervention_days: number | null;
  adherence: string | null;
  adverse_events: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface FollowupOutcome {
  id?: number;
  followup_date: string | null;
  primary_outcome: string | null;
  secondary_outcome: string | null;
  notes: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface PredictionResult {
  id?: number;
  data_completeness_score?: number | null;
  benefit_score?: number | null;
  recommendation_level: string | null;
  score: number | null;
  explanation_text: string | null;
  key_factors?: string[];
  usage_limitations?: string[];
  engine_name?: string | null;
  engine_version?: string | null;
  rule_snapshot?: Record<string, unknown> | null;
  generated_at: string | null;
  created_at?: string;
  updated_at?: string;
  model_version: {
    id: number;
    name: string;
    version_type: string;
    status: string;
    description: string | null;
  } | null;
}

export interface PatientDetail extends PatientListItem {
  baseline_feature: BaselineFeature | null;
  questionnaire_score: QuestionnaireScore | null;
  sleep_metric: SleepMetric | null;
  light_intervention: LightIntervention | null;
  followup_outcome: FollowupOutcome | null;
  prediction_result: PredictionResult | null;
}

export interface PatientListResponse {
  items: PatientListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface PatientQueryParams {
  page: number;
  page_size: number;
  keyword?: string;
  ids?: number[];
  gender?: string;
  has_baseline_feature?: boolean;
  has_light_intervention?: boolean;
  has_followup_outcome?: boolean;
}

export interface PatientCreatePayload {
  patient_code: string;
  anonymized_code: string;
  gender: string | null;
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  education_level: string | null;
  remarks: string | null;
}

export interface QualityPatientIssue {
  patient_id: number | null;
  patient_code: string | null;
  anonymized_code: string | null;
  issue_code: string;
  issue_type: string;
  section: string;
  severity: string;
  message: string;
  suggested_action: string;
  blocking: boolean;
}

export interface QualitySuggestedFix {
  issue_code: string;
  title: string;
  description: string;
  priority: string;
  patient_count: number;
  affected_patient_ids: number[];
}

export interface DataQualityResponse {
  summary: {
    total_patients: number;
    complete_patients: number;
    modeling_ready_patients: number;
    blocking_issue_count: number;
    warning_issue_count: number;
    affected_patient_count: number;
    average_completion_rate: number;
    missing_fields: Array<{
      field_label: string;
      missing_count: number;
      missing_rate: number;
    }>;
    completion_stats: Array<{
      field_label: string;
      completed_count: number;
      completion_rate: number;
    }>;
    gender_distribution: Array<{ name: string; value: number }>;
    section_completion: Array<{ name: string; value: number }>;
    age_bucket_distribution: Array<{ name: string; value: number }>;
  };
  blocking_issues: QualityPatientIssue[];
  warning_issues: QualityPatientIssue[];
  suggested_fixes: QualitySuggestedFix[];
  affected_patient_ids: number[];
}

export async function fetchPatients(params: PatientQueryParams) {
  const { data } = await apiClient.get<PatientListResponse>('/patients', { params });
  return data;
}

export async function fetchPatientDetail(patientId: number) {
  const { data } = await apiClient.get<PatientDetail>(`/patients/${patientId}`);
  return data;
}

export async function createPatient(payload: PatientCreatePayload) {
  const { data } = await apiClient.post<PatientDetail>('/patients', payload);
  return data;
}

export async function updatePatientBasic(patientId: number, payload: Partial<PatientCreatePayload>) {
  const { data } = await apiClient.put<PatientDetail>(`/patients/${patientId}`, payload);
  return data;
}

export async function saveBaselineFeature(patientId: number, payload: BaselineFeature) {
  const { data } = await apiClient.put<PatientDetail>(`/patients/${patientId}/baseline-feature`, payload);
  return data;
}

export async function saveQuestionnaireScore(patientId: number, payload: QuestionnaireScore) {
  const { data } = await apiClient.put<PatientDetail>(`/patients/${patientId}/questionnaire-score`, payload);
  return data;
}

export async function saveSleepMetric(patientId: number, payload: SleepMetric) {
  const { data } = await apiClient.put<PatientDetail>(`/patients/${patientId}/sleep-metric`, payload);
  return data;
}

export async function saveLightIntervention(patientId: number, payload: LightIntervention) {
  const { data } = await apiClient.put<PatientDetail>(`/patients/${patientId}/light-intervention`, payload);
  return data;
}

export async function saveFollowupOutcome(patientId: number, payload: FollowupOutcome) {
  const { data } = await apiClient.put<PatientDetail>(`/patients/${patientId}/followup-outcome`, payload);
  return data;
}

export async function fetchQualitySummary() {
  const { data } = await apiClient.get<DataQualityResponse>('/quality/summary');
  return data;
}
