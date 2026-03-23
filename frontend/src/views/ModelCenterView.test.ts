import { flushPromises, mount } from '@vue/test-utils';
import ElementPlus from 'element-plus';
import { createPinia } from 'pinia';
import { createMemoryHistory, createRouter } from 'vue-router';
import { vi } from 'vitest';

import ModelCenterView from '@/views/ModelCenterView.vue';

const modelCenterMocks = vi.hoisted(() => ({
  fetchCausalDatasetOverview: vi.fn(),
  fetchModelVersions: vi.fn(),
  fetchActiveModel: vi.fn(),
  trainCausalModel: vi.fn(),
  activateModelVersion: vi.fn(),
  fetchQualitySummary: vi.fn(),
}));

vi.mock('@/api/modelCenter', () => ({
  activateModelVersion: modelCenterMocks.activateModelVersion,
  fetchActiveModel: modelCenterMocks.fetchActiveModel,
  fetchCausalDatasetOverview: modelCenterMocks.fetchCausalDatasetOverview,
  fetchModelVersions: modelCenterMocks.fetchModelVersions,
  trainCausalModel: modelCenterMocks.trainCausalModel,
}));

vi.mock('@/api/subjects', () => ({
  fetchQualitySummary: modelCenterMocks.fetchQualitySummary,
}));

describe('ModelCenterView', () => {
  beforeEach(() => {
    modelCenterMocks.fetchCausalDatasetOverview.mockResolvedValue({
      total_patients: 20,
      eligible_records: 12,
      dropped_records: 8,
      selected_feature_names: ['年龄', 'PSQI'],
      treatment_name: '增强光干预方案',
      control_name: '标准光干预方案',
      outcome_name: '随访主要结局改善值',
      treatment_distribution: [],
      outcome_summary: { min_value: 1, max_value: 8, mean_value: 4 },
      feature_coverage: [],
      dropped_examples: [],
      assumptions: [],
      limitations: [],
    });
    modelCenterMocks.fetchModelVersions.mockResolvedValue([]);
    modelCenterMocks.fetchActiveModel.mockResolvedValue({ active_model: null });
    modelCenterMocks.fetchQualitySummary.mockResolvedValue({
      summary: {
        total_patients: 20,
        complete_patients: 12,
        modeling_ready_patients: 12,
        blocking_issue_count: 0,
        warning_issue_count: 2,
        affected_patient_count: 2,
        average_completion_rate: 80,
        missing_fields: [],
        completion_stats: [],
        gender_distribution: [],
        section_completion: [],
        age_bucket_distribution: [],
      },
      blocking_issues: [],
      warning_issues: [],
      suggested_fixes: [],
      affected_patient_ids: [1, 2],
    });
    modelCenterMocks.trainCausalModel.mockResolvedValue({
      message: '训练完成',
      model_version: {
        id: 1,
        name: '测试模型',
        version_type: 'causal',
        status: 'active',
        description: null,
        artifact_path: 'app/model_artifacts/test.json',
        engine_backend: 'fallback_nearest_neighbor',
        estimator_message: 'fallback',
        reproducibility_status: 'fallback_demo',
        metrics: {},
        config: {},
        feature_list: ['age'],
        selected_feature_keys: ['age'],
        random_seed: 20260319,
        test_ratio: 0.2,
        min_feature_coverage: 0.7,
        artifact_generated_at: '2026-03-19T00:00:00Z',
        training_started_at: '2026-03-19T00:00:00Z',
        training_completed_at: '2026-03-19T00:00:00Z',
        created_at: '2026-03-19T00:00:00Z',
        updated_at: '2026-03-19T00:00:00Z',
      },
      result: {
        model_version: {},
        ate: 1.2,
        validation_ate: 1,
        observed_group_difference: 0.8,
        engine_backend: 'fallback_nearest_neighbor',
        estimator_message: 'fallback',
        reproducibility_status: 'fallback_demo',
        dataset_record_count: 12,
        train_record_count: 10,
        validation_record_count: 2,
        treatment_name: '增强光干预方案',
        control_name: '标准光干预方案',
        outcome_name: '随访主要结局改善值',
        selected_feature_names: ['年龄'],
        selected_feature_keys: ['age'],
        random_seed: 20260319,
        test_ratio: 0.2,
        min_feature_coverage: 0.7,
        artifact_generated_at: '2026-03-19T00:00:00Z',
        ite_distribution: [],
        feature_importance: [],
        subgroup_results: [],
        top_positive_patients: [],
        top_negative_patients: [],
        assumptions: [],
        limitations: [],
      },
    });
  });

  it('builds training payload with trimmed feature names', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div />' } },
        { path: '/causal-results', component: { template: '<div />' } },
        { path: '/data-quality', component: { template: '<div />' } },
      ],
    });
    await router.push('/');
    await router.isReady();

    const wrapper = mount(ModelCenterView, {
      global: {
        plugins: [createPinia(), router, ElementPlus],
      },
    });

    await flushPromises();

    const setupState = (wrapper.vm.$ as any).setupState as Record<string, unknown>;
    setupState.featureNamesText = 'age, psqi_score , isi_score';
    const trainForm = setupState.trainForm as Record<string, unknown>;
    trainForm.model_name = '新模型';
    trainForm.test_ratio = 0.3;
    trainForm.random_seed = 20260320;
    trainForm.max_features = 9;
    trainForm.min_feature_coverage = 0.75;

    await (setupState.handleTrain as () => Promise<void>)();
    await flushPromises();

    expect(modelCenterMocks.trainCausalModel).toHaveBeenCalledWith({
      model_name: '新模型',
      test_ratio: 0.3,
      random_seed: 20260320,
      max_features: 9,
      min_feature_coverage: 0.75,
      feature_names: ['age', 'psqi_score', 'isi_score'],
      activate_after_train: true,
    });
  });
});
