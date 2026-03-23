import apiClient from '@/api/client';

export interface RecommendationEvaluationResult {
  patient_id: number;
  patient_code: string;
  anonymized_code: string;
  generated_at: string;
  data_completeness_score: number;
  benefit_score: number;
  recommendation_level: string;
  explanation_text: string;
  key_factors: string[];
  usage_limitations: string[];
  engine_name: string;
  engine_version: string;
  saved: boolean;
  model_version_name: string;
  rule_snapshot: Record<string, unknown>;
}

export interface RecommendationHistoryItem {
  patient_id: number;
  patient_code: string;
  anonymized_code: string;
  recommendation_level: string | null;
  benefit_score: number | null;
  data_completeness_score: number | null;
  engine_name: string | null;
  engine_version: string | null;
  generated_at: string | null;
  updated_at: string;
  explanation_text: string | null;
}

export interface RecommendationHistoryResponse {
  items: RecommendationHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface BatchEvaluateResponse {
  total_requested: number;
  success_count: number;
  failed_count: number;
  results: RecommendationEvaluationResult[];
  errors: string[];
}

export interface RecommendationConfig {
  engine_name: string;
  engine_version: string;
  model_version_name: string;
  base_benefit_score: number;
  thresholds: {
    recommend_min_score: number;
    cautious_min_score: number;
    min_completeness_for_recommend: number;
    min_completeness_for_cautious: number;
  };
  completeness_fields: Array<{
    label: string;
    path: string;
    weight: number;
  }>;
  score_rules: Array<{
    id: string;
    label: string;
    field_path: string;
    operator: string;
    value: string | number;
    score_delta: number;
    factor_text: string;
  }>;
  limitation_templates: string[];
  report_footer_notice: string;
}

export async function evaluateSinglePatient(patientId: number, saveResult = true) {
  const { data } = await apiClient.post<RecommendationEvaluationResult>(
    `/recommendations/evaluate/${patientId}`,
    null,
    { params: { save_result: saveResult } },
  );
  return data;
}

export async function evaluateBatchPatients(patientIds: number[], saveResult = true) {
  const { data } = await apiClient.post<BatchEvaluateResponse>('/recommendations/evaluate-batch', {
    patient_ids: patientIds,
    save_result: saveResult,
  });
  return data;
}

export async function fetchRecommendationHistory(params: {
  page: number;
  page_size: number;
  keyword?: string;
  level?: string;
}) {
  const { data } = await apiClient.get<RecommendationHistoryResponse>('/recommendations/history', {
    params,
  });
  return data;
}

export async function fetchRecommendationConfig() {
  const { data } = await apiClient.get<RecommendationConfig>('/system-settings/recommendation-rules');
  return data;
}

export async function saveRecommendationConfig(payload: RecommendationConfig) {
  const { data } = await apiClient.put<RecommendationConfig>('/system-settings/recommendation-rules', payload);
  return data;
}

export async function fetchReportPreview(patientId: number, autoGenerate = true) {
  const { data } = await apiClient.get(`/reports/preview/${patientId}`, {
    params: { auto_generate: autoGenerate },
  });
  return data;
}

export async function fetchReportHtml(patientId: number, autoGenerate = true) {
  const { data } = await apiClient.get<string>(`/reports/html/${patientId}`, {
    params: { auto_generate: autoGenerate },
    responseType: 'text',
  });
  return data;
}

export async function openPrintReport(patientId: number, autoGenerate = true) {
  const printWindow = window.open('', '_blank', 'noopener,noreferrer');
  if (!printWindow) {
    return;
  }

  const html = await fetchReportHtml(patientId, autoGenerate);
  printWindow.document.open();
  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
}

export async function downloadReportExportList(keyword?: string, level?: string) {
  const response = await apiClient.get('/reports/export-list.csv', {
    params: { keyword, level },
    responseType: 'blob',
  });
  const blob = new Blob([response.data]);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'recommendation_report_list.csv';
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
