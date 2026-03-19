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
}

export interface PatientListResponse {
  items: PatientListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface ImportErrorItem {
  row_number: number;
  patient_code: string | null;
  message: string;
}

export interface ImportResponse {
  message: string;
  summary: {
    total_rows: number;
    success_count: number;
    failed_count: number;
    created_count: number;
    updated_count: number;
  };
  errors: ImportErrorItem[];
}

export interface ImportHistoryItem {
  id: number;
  actor_name: string;
  file_name: string | null;
  action_type: string;
  target_type: string;
  target_id: string | null;
  occurred_at: string;
  detail_text: string | null;
  total_rows: number | null;
  success_count: number | null;
  failed_count: number | null;
}

export async function fetchPatients(params: { page: number; page_size: number; keyword?: string }) {
  const { data } = await apiClient.get<PatientListResponse>('/patients', { params });
  return data;
}

export async function fetchImportHistory(limit = 10) {
  const { data } = await apiClient.get<{ items: ImportHistoryItem[] }>('/imports/history', {
    params: { limit },
  });
  return data.items;
}

export async function uploadPatientFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<ImportResponse>('/imports/patients', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
}

export async function downloadTemplate(format: 'csv' | 'xlsx') {
  const response = await apiClient.get('/imports/template', {
    params: { format },
    responseType: 'blob',
  });

  const blob = new Blob([response.data]);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  const filename = format === 'csv' ? 'patients_import_template.csv' : 'patients_import_template.xlsx';
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
