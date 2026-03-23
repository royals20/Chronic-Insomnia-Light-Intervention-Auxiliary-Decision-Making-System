import { flushPromises, mount } from '@vue/test-utils';
import ElementPlus from 'element-plus';
import { createMemoryHistory, createRouter } from 'vue-router';
import { vi } from 'vitest';

import CausalResultsView from '@/views/CausalResultsView.vue';

const chartInstance = {
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
};

vi.mock('echarts', () => ({
  init: vi.fn(() => chartInstance),
}));

const causalMocks = vi.hoisted(() => ({
  fetchModelVersions: vi.fn(),
  fetchCausalResults: vi.fn(),
}));

vi.mock('@/api/modelCenter', () => ({
  fetchModelVersions: causalMocks.fetchModelVersions,
  fetchCausalResults: causalMocks.fetchCausalResults,
}));

describe('CausalResultsView', () => {
  beforeEach(() => {
    causalMocks.fetchModelVersions.mockResolvedValue([
      {
        id: 1,
        name: '因果模型 A',
        version_type: 'causal',
        status: 'active',
        description: '测试模型',
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
    ]);

    causalMocks.fetchCausalResults.mockResolvedValue({
      model_version: {
        id: 1,
        name: '因果模型 A',
        version_type: 'causal',
        status: 'active',
        description: '测试模型',
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
      ate: 1.2,
      validation_ate: 1.0,
      observed_group_difference: 0.8,
      engine_backend: 'fallback_nearest_neighbor',
      estimator_message: '当前环境使用 fallback 估计器',
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
      ite_distribution: [
        { name: '0-1', value: 2 },
        { name: '1-2', value: 4 },
      ],
      feature_importance: [
        { feature_name: 'age', feature_label: '年龄', importance: 0.42 },
      ],
      subgroup_results: [
        { feature_name: 'gender', feature_label: '性别', subgroup_name: '女性', sample_count: 6, average_ite: 1.4 },
      ],
      top_positive_patients: [
        { patient_id: 1, patient_code: 'P001', anonymized_code: 'A001', treatment_label: '增强光干预方案', observed_outcome: 4, estimated_ite: 1.8 },
      ],
      top_negative_patients: [
        { patient_id: 2, patient_code: 'P002', anonymized_code: 'A002', treatment_label: '标准光干预方案', observed_outcome: 2, estimated_ite: -0.4 },
      ],
      assumptions: ['样本满足可交换性假设'],
      limitations: ['仅供科研分析'],
    });
  });

  it('renders the narrative sections after loading a model result', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div />' } },
        { path: '/model-center', component: { template: '<div />' } },
      ],
    });

    await router.push('/?modelVersionId=1');
    await router.isReady();

    const wrapper = mount(CausalResultsView, {
      global: {
        plugins: [router, ElementPlus],
      },
    });

    await flushPromises();

    expect(causalMocks.fetchCausalResults).toHaveBeenCalledWith(1);
    expect(wrapper.text()).toContain('因果获益评估叙事页');
    expect(wrapper.text()).toContain('总体结论');
    expect(wrapper.text()).toContain('解释证据');
    expect(wrapper.text()).toContain('增强光干预方案');
    expect(wrapper.text()).toContain('标准光干预方案');
    expect(wrapper.text()).toContain('呈正向平均效应');
  });
});
