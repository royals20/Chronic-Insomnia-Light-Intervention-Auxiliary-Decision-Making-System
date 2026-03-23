import apiClient from '@/api/client';

export interface FeatureCoverageItem {
  feature_name: string;
  feature_label: string;
  available_count: number;
  missing_count: number;
  coverage_rate: number;
  variance: number;
  selected: boolean;
}

export interface ValueCountItem {
  name: string;
  value: number;
}

export interface OutcomeSummary {
  min_value: number;
  max_value: number;
  mean_value: number;
}

export interface DatasetOverviewResponse {
  total_patients: number;
  eligible_records: number;
  dropped_records: number;
  selected_feature_names: string[];
  treatment_name: string;
  control_name: string;
  outcome_name: string;
  treatment_distribution: ValueCountItem[];
  outcome_summary: OutcomeSummary | null;
  feature_coverage: FeatureCoverageItem[];
  dropped_examples: string[];
  assumptions: string[];
  limitations: string[];
}

export interface CausalTrainingRequest {
  model_name?: string;
  test_ratio: number;
  random_seed: number;
  max_features: number;
  min_feature_coverage: number;
  feature_names?: string[];
  activate_after_train: boolean;
}

export interface ModelVersionSummary {
  id: number;
  name: string;
  version_type: string;
  status: string;
  description: string | null;
  artifact_path: string | null;
  engine_backend: string | null;
  estimator_message: string | null;
  reproducibility_status: string | null;
  metrics: Record<string, unknown>;
  config: Record<string, unknown>;
  feature_list: string[];
  selected_feature_keys: string[];
  random_seed: number | null;
  test_ratio: number | null;
  min_feature_coverage: number | null;
  artifact_generated_at: string | null;
  training_started_at: string | null;
  training_completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ActiveModelResponse {
  active_model: ModelVersionSummary | null;
}

export interface HistogramBucket {
  name: string;
  value: number;
}

export interface FeatureImportanceItem {
  feature_name: string;
  feature_label: string;
  importance: number;
}

export interface SubgroupResultItem {
  feature_name: string;
  feature_label: string;
  subgroup_name: string;
  sample_count: number;
  average_ite: number;
}

export interface PatientEffectItem {
  patient_id: number;
  patient_code: string;
  anonymized_code: string;
  treatment_label: string;
  observed_outcome: number;
  estimated_ite: number;
}

export interface CausalEvaluationResultResponse {
  model_version: ModelVersionSummary;
  ate: number;
  validation_ate: number | null;
  observed_group_difference: number | null;
  engine_backend: string;
  estimator_message: string;
  reproducibility_status: string;
  dataset_record_count: number;
  train_record_count: number;
  validation_record_count: number;
  treatment_name: string;
  control_name: string;
  outcome_name: string;
  selected_feature_names: string[];
  selected_feature_keys: string[];
  random_seed: number | null;
  test_ratio: number | null;
  min_feature_coverage: number | null;
  artifact_generated_at: string | null;
  ite_distribution: HistogramBucket[];
  feature_importance: FeatureImportanceItem[];
  subgroup_results: SubgroupResultItem[];
  top_positive_patients: PatientEffectItem[];
  top_negative_patients: PatientEffectItem[];
  assumptions: string[];
  limitations: string[];
}

export interface CausalTrainingResponse {
  message: string;
  model_version: ModelVersionSummary;
  result: CausalEvaluationResultResponse;
}

export async function fetchCausalDatasetOverview(params?: {
  max_features?: number;
  min_feature_coverage?: number;
}) {
  const { data } = await apiClient.get<DatasetOverviewResponse>('/model-center/dataset-overview', {
    params,
  });
  return data;
}

export async function trainCausalModel(payload: CausalTrainingRequest) {
  const { data } = await apiClient.post<CausalTrainingResponse>('/model-center/train', payload);
  return data;
}

export async function fetchModelVersions(versionType?: string) {
  const { data } = await apiClient.get<ModelVersionSummary[]>('/model-center/versions', {
    params: {
      version_type: versionType,
    },
  });
  return data;
}

export async function fetchActiveModel(versionType = 'causal') {
  const { data } = await apiClient.get<ActiveModelResponse>('/model-center/active-model', {
    params: {
      version_type: versionType,
    },
  });
  return data;
}

export async function activateModelVersion(versionId: number) {
  const { data } = await apiClient.post<ModelVersionSummary>(`/model-center/versions/${versionId}/activate`);
  return data;
}

export async function fetchCausalResults(modelVersionId?: number) {
  const { data } = await apiClient.get<CausalEvaluationResultResponse>('/model-center/causal-results', {
    params: {
      model_version_id: modelVersionId,
    },
  });
  return data;
}
