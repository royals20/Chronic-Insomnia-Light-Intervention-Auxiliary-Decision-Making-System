<template>
  <div>
    <DisclaimerBanner />

    <el-row :gutter="20" class="stats-row">
      <el-col v-for="item in statistics" :key="item.label" :xs="24" :sm="12" :lg="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card__head">
            <span>{{ item.label }}</span>
            <el-tag :type="item.tagType" effect="light">{{ item.tag }}</el-tag>
          </div>
          <div class="stat-card__value">{{ item.value }}</div>
          <p class="stat-card__desc">{{ item.description }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>最近 7 日导入趋势</span>
              <span class="sub-text">模拟科研数据</span>
            </div>
          </template>
          <div ref="chartRef" class="chart-box"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>最近导入记录</span>
              <span class="sub-text">按时间倒序</span>
            </div>
          </template>

          <el-table :data="recentImports" stripe>
            <el-table-column prop="batchNo" label="批次编号" min-width="120" />
            <el-table-column prop="operator" label="操作人" min-width="90" />
            <el-table-column prop="importedAt" label="导入时间" min-width="150" />
            <el-table-column prop="count" label="病例数" width="80" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts';
import { onBeforeUnmount, onMounted, ref } from 'vue';

import DisclaimerBanner from '@/components/DisclaimerBanner.vue';

interface StatisticItem {
  label: string;
  value: number;
  description: string;
  tag: string;
  tagType: '' | 'success' | 'warning' | 'info' | 'primary' | 'danger';
}

interface ImportRecord {
  batchNo: string;
  operator: string;
  importedAt: string;
  count: number;
}

const statistics: StatisticItem[] = [
  {
    label: '病例总数',
    value: 128,
    description: '当前纳入科研原型数据库的模拟病例总量',
    tag: '累计纳入',
    tagType: 'primary',
  },
  {
    label: '已完成基线评估人数',
    value: 96,
    description: '已完成基线量表录入与整理的模拟人数',
    tag: '评估完成',
    tagType: 'success',
  },
  {
    label: '已生成推荐人数',
    value: 74,
    description: '已生成演示推荐结果的模拟人数',
    tag: '推荐生成',
    tagType: 'warning',
  },
];

const recentImports: ImportRecord[] = [
  {
    batchNo: 'IMP-20260319-01',
    operator: '王研究员',
    importedAt: '2026-03-19 09:20',
    count: 12,
  },
  {
    batchNo: 'IMP-20260318-02',
    operator: '李同学',
    importedAt: '2026-03-18 16:40',
    count: 18,
  },
  {
    batchNo: 'IMP-20260318-01',
    operator: '张医生',
    importedAt: '2026-03-18 10:15',
    count: 9,
  },
  {
    batchNo: 'IMP-20260317-03',
    operator: '王研究员',
    importedAt: '2026-03-17 14:05',
    count: 21,
  },
];

const chartRef = ref<HTMLElement | null>(null);
let chart: echarts.ECharts | null = null;

function resizeChart() {
  chart?.resize();
}

onMounted(() => {
  if (!chartRef.value) {
    return;
  }

  chart = echarts.init(chartRef.value);
  chart.setOption({
    tooltip: {
      trigger: 'axis',
    },
    grid: {
      left: 40,
      right: 20,
      top: 30,
      bottom: 30,
    },
    xAxis: {
      type: 'category',
      data: ['03-13', '03-14', '03-15', '03-16', '03-17', '03-18', '03-19'],
      boundaryGap: false,
      axisLine: {
        lineStyle: {
          color: '#b7c4d3',
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '导入人数',
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#e1e8f0',
        },
      },
    },
    series: [
      {
        name: '导入病例数',
        type: 'line',
        smooth: true,
        data: [10, 12, 9, 15, 18, 21, 12],
        lineStyle: {
          color: '#1677c8',
          width: 3,
        },
        itemStyle: {
          color: '#1677c8',
        },
        areaStyle: {
          color: 'rgba(22, 119, 200, 0.16)',
        },
      },
    ],
  });

  window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  chart?.dispose();
  chart = null;
});
</script>

<style scoped>
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 16px;
}

.stat-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #506273;
  font-size: 14px;
}

.stat-card__value {
  margin: 16px 0 8px;
  font-size: 34px;
  line-height: 1;
  font-weight: 700;
  color: #143b63;
}

.stat-card__desc {
  margin: 0;
  color: #738496;
  font-size: 13px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.sub-text {
  color: #7f8fa2;
  font-size: 13px;
  font-weight: 400;
}

.chart-box {
  height: 320px;
}
</style>
