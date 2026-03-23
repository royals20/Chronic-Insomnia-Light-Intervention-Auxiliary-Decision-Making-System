import { flushPromises, mount } from '@vue/test-utils';
import ElementPlus from 'element-plus';
import { createPinia } from 'pinia';
import { createMemoryHistory, createRouter } from 'vue-router';
import { vi } from 'vitest';

import RecommendationCenterView from '@/views/RecommendationCenterView.vue';

const recommendationMocks = vi.hoisted(() => ({
  fetchPatients: vi.fn(),
  fetchRecommendationHistory: vi.fn(),
  evaluateSinglePatient: vi.fn(),
}));

vi.mock('@/api/subjects', () => ({
  fetchPatients: recommendationMocks.fetchPatients,
}));

vi.mock('@/api/recommendation', () => ({
  evaluateBatchPatients: vi.fn(),
  evaluateSinglePatient: recommendationMocks.evaluateSinglePatient,
  fetchRecommendationHistory: recommendationMocks.fetchRecommendationHistory,
}));

describe('RecommendationCenterView', () => {
  beforeEach(() => {
    recommendationMocks.fetchPatients.mockResolvedValue({
      items: [
        {
          id: 1,
          patient_code: 'P001',
          anonymized_code: 'A001',
          gender: '女',
          age: 33,
          has_questionnaire_score: true,
          has_sleep_metric: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 300,
    });
    recommendationMocks.fetchRecommendationHistory.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    });
    recommendationMocks.evaluateSinglePatient.mockResolvedValue({
      patient_id: 1,
      patient_code: 'P001',
      anonymized_code: 'A001',
      generated_at: '2026-03-19T00:00:00Z',
      data_completeness_score: 88,
      benefit_score: 92,
      recommendation_level: '推荐光干预',
      explanation_text: '测试说明',
      key_factors: ['ISI 评分提示失眠症状较明显'],
      usage_limitations: ['仅供科研辅助'],
      engine_name: '规则/评分版推荐引擎',
      engine_version: 'V1',
      saved: true,
      model_version_name: '规则评分引擎V1',
      rule_snapshot: {},
    });
  });

  it('submits single-patient evaluation and renders the result', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div />' } },
        { path: '/report-center', component: { template: '<div />' } },
        { path: '/subjects/:id', component: { template: '<div />' } },
        { path: '/model-center', component: { template: '<div />' } },
      ],
    });
    await router.push('/');
    await router.isReady();

    const wrapper = mount(RecommendationCenterView, {
      global: {
        plugins: [createPinia(), router, ElementPlus],
      },
    });

    await flushPromises();

    const setupState = (wrapper.vm.$ as any).setupState as Record<string, unknown>;
    setupState.selectedPatientId = 1;
    await (setupState.runSingle as (saveResult: boolean) => Promise<void>)(true);
    await flushPromises();

    expect(recommendationMocks.evaluateSinglePatient).toHaveBeenCalledWith(1, true);
    expect(wrapper.text()).toContain('推荐光干预');
    expect(wrapper.text()).toContain('规则/评分版推荐引擎');
  });
});
