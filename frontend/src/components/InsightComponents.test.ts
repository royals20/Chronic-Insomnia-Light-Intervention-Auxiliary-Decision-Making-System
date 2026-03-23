import { mount } from '@vue/test-utils';

import DataBadge from '@/components/DataBadge.vue';
import InsightHero from '@/components/InsightHero.vue';
import NarrativePanel from '@/components/NarrativePanel.vue';

describe('analysis display components', () => {
  it('renders a data badge with the provided label', () => {
    const wrapper = mount(DataBadge, {
      props: {
        label: '真实估计器',
        tone: 'success',
      },
    });

    expect(wrapper.text()).toContain('真实估计器');
    expect(wrapper.attributes('data-tone')).toBe('success');
  });

  it('renders hero meta actions and aside slots', () => {
    const wrapper = mount(InsightHero, {
      props: {
        eyebrow: 'Model Lab',
        title: '因果训练驾驶舱',
        description: '说明文本',
      },
      slots: {
        meta: '<span>元信息</span>',
        actions: '<button>开始</button>',
        aside: '<div>侧边摘要</div>',
      },
    });

    expect(wrapper.text()).toContain('因果训练驾驶舱');
    expect(wrapper.text()).toContain('元信息');
    expect(wrapper.text()).toContain('开始');
    expect(wrapper.text()).toContain('侧边摘要');
  });

  it('renders narrative panel content and footer', () => {
    const wrapper = mount(NarrativePanel, {
      props: {
        title: '总体结论',
        description: '先看结论再看证据',
      },
      slots: {
        default: '<div>面板内容</div>',
        footer: '<button>下一步</button>',
      },
    });

    expect(wrapper.text()).toContain('总体结论');
    expect(wrapper.text()).toContain('面板内容');
    expect(wrapper.text()).toContain('下一步');
  });
});
