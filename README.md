# 慢性失眠光干预科研辅助决策系统科研平台化原型

本项目是一个面向硕士论文、科研演示、实验复现和软件著作权申请的单仓库科研平台化原型系统，用于展示“慢性失眠光干预科研辅助决策系统”的基础数据层、规则推荐链路、数据质量治理、报告流程和因果获益评估流程。

> 说明：本系统仅供科研辅助，不替代临床诊断与治疗。

## 项目定位

- 当前目标：提供一个可运行、可演示、可复现、可扩展的科研平台化原型。
- 适用场景：论文展示、科研汇报、课题中期检查、软著材料准备、方法学演示与实验记录。
- 非目标：真实 HIS 对接、设备实时接入、移动端、正式临床决策支持。

## 技术栈

- 后端：FastAPI + SQLAlchemy + Pydantic + SQLite
- 前端：Vue3 + Vite + TypeScript + Element Plus + Pinia + Vue Router + ECharts
- 测试与校验：Pytest + Vitest + GitHub Actions
- 启动方式：本地开发 + Docker Compose

## 目录结构

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/routes/              # 路由：认证、患者、导入、推荐、模型中心等
│  │  ├─ config_data/             # 推荐规则 JSON 配置
│  │  ├─ core/                    # 配置
│  │  ├─ db/                      # 数据库会话与初始化
│  │  ├─ modeling/                # 因果获益评估模块：数据读取、特征选择、拆分、估计器接口
│  │  ├─ model_artifacts/         # 因果模型训练产物（运行时生成）
│  │  ├─ models/                  # SQLAlchemy 模型
│  │  ├─ schemas/                 # Pydantic Schema
│  │  └─ services/                # 业务服务
│  ├─ scripts/
│  │  ├─ init_db.py
│  │  └─ seed_demo_data.py
│  ├─ .env.example
│  ├─ Dockerfile
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ components/
│  │  ├─ layouts/
│  │  ├─ router/
│  │  ├─ stores/
│  │  ├─ utils/
│  │  └─ views/
│  ├─ Dockerfile
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.ts
├─ docs/
│  ├─ architecture.md
│  └─ screenshots/
├─ scripts/
│  ├─ init-db.ps1
│  ├─ seed-demo-data.ps1
│  ├─ start-backend.ps1
│  └─ start-frontend.ps1
└─ docker-compose.yml
```

## 演示账号

- 用户名：`research_demo`
- 密码：`Demo@123456`

## 数据库核心表

当前版本已经建立以下 10 张核心表：

1. `users`
2. `patients`
3. `baseline_features`
4. `questionnaire_scores`
5. `sleep_metrics`
6. `light_interventions`
7. `followup_outcomes`
8. `prediction_results`
9. `model_versions`
10. `audit_logs`

### 关键字段概览

- `patients`：患者编号、匿名编号、性别、年龄、身高、体重、教育程度、备注
- `baseline_features`：作息、病程、用药、合并症、心理状态、睡眠习惯、备注
- `questionnaire_scores`：PSQI、ISI、焦虑评分、抑郁评分、评估日期
- `sleep_metrics`：总睡眠时间、入睡潜伏期、睡眠效率、觉醒次数、备注
- `light_interventions`：光照强度、开始时段、持续时间、天数、依从性、不良反应
- `followup_outcomes`：随访日期、主要结局、次要结局、备注
- `prediction_results`：数据完整性评分、推荐等级、评分、解释文本、关键因素、限制说明、模型版本、生成时间
- `model_versions`：名称、类型（`rule / predictive / causal`）、状态、说明、训练元数据、产物路径
- `audit_logs`：操作人、操作类型、目标对象、时间、详情

## 本地初始化

### 1. 创建虚拟环境并安装后端依赖

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### 2. 初始化数据库

```powershell
.\scripts\init-db.ps1
```

或：

```powershell
cd backend
.venv\Scripts\python scripts\init_db.py
```

### 3. 写入 100 例模拟数据

```powershell
.\scripts\seed-demo-data.ps1
```

或：

```powershell
cd backend
.venv\Scripts\python scripts\seed_demo_data.py
```

## 启动方式

### 后端

```powershell
cd backend
.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 健康检查：[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- API 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 前端

```powershell
cd frontend
npm install --cache .npm-cache
npm run dev
```

- 前端页面：[http://127.0.0.1:5173](http://127.0.0.1:5173)

### Docker Compose

```powershell
docker-compose -p insomnia-research up --build
```

## 测试与校验

### 后端测试

```powershell
cd backend
.venv\Scripts\python -m pytest
```

### 前端测试

```powershell
cd frontend
npm run test
```

### 前端类型检查与构建

```powershell
cd frontend
npm run build
```

> 说明：当前仓库已补充基础后端测试、前端单测与 `.github/workflows/ci.yml` 持续集成流程。

## 当前主要页面

- 登录页
- Dashboard
- 数据中心
- 受试者列表页
- 受试者详情页
- 基线特征录入页
- 量表录入页
- 客观睡眠指标录入页
- 光干预记录页
- 随访结局录入页
- 数据质量检查页
- 评估/推荐中心
- 报告中心
- 模型中心
- 因果评估结果页
- 系统设置页

## 当前演示能力

### 0. 数据质量与实验地基

- 数据质量页输出结构化 `summary / blocking_issues / warning_issues / suggested_fixes / affected_patient_ids`
- 支持字段合法性、跨表一致性、建模可用性三层检查
- 数据中心支持按“待补录/复核受试者”联动筛选
- 模型中心在训练前直接提示阻塞性数据问题

### 1. 规则/评分版推荐引擎

- 配置来源：`backend/app/config_data/recommendation_rules.json`
- 输出内容：
  - 数据完整性评分
  - 获益评分（0-100）
  - 推荐等级
  - 关键影响因素
  - 使用限制说明
- 保存位置：`prediction_results`
- 适用说明：仅为 V1 原型规则引擎，不代表正式临床模型

### 2. 报告中心

- 支持单例报告预览
- 支持批量导出清单
- 支持打印友好的 HTML 报告模板
- 报告固定展示：
  - 基本信息
  - 数据完整性
  - 推荐等级
  - 关键因素
  - 限制说明
  - “仅供科研辅助，不替代临床诊断与治疗”

### 3. 因果获益评估模式

后端新增独立 `modeling` 模块，支持：

- 数据读取
- 特征选择
- 训练/验证拆分
- 因果模型抽象接口
- 可替换的估计器实现

当前实现说明：

- 优先尝试真实因果估计器风格接口
- 若本地缺少复杂依赖，则自动降级到可运行的 fallback 估计器
- 训练结果会记录随机种子、特征键、覆盖率阈值、训练/验证拆分信息与复现状态
- 模型版本仍保存为 `causal` 类型，页面和接口流程保持不变

## Causal 模式的数据要求

因果模式要求明确区分以下三类变量：

### X：基线协变量

应来自干预前信息，例如：

- 年龄、性别、BMI
- 病程
- 用药情况
- 心理状态
- 基线量表分数（PSQI、ISI、焦虑、抑郁）
- 基线睡眠指标（总睡眠时间、入睡潜伏期、睡眠效率、觉醒次数）

### T：处理变量

必须是可比较的处理定义，例如：

- 光干预 vs 常规治疗
- 高强度光干预 vs 标准光干预
- 方案 A vs 方案 B

当前演示默认将 `T` 定义为：

- `增强光干预方案`
- 对比 `标准光干预方案`

该划分根据 `light_interventions` 中的强度、持续时间和天数自动生成，仅用于演示。

### Y：结局变量

必须是明确、可比较、可量化的结果指标，例如：

- ISI 改善值
- PSQI 改善值
- 睡眠效率提升值
- 主要结局改善值

当前演示默认将 `Y` 定义为：

- 从 `followup_outcomes.primary_outcome` 中提取的改善数值
- 若主要结局缺失，则退回次要结局中的数值

## 因果前提与限制

因果结果只有在以下前提近似成立时才有解释价值：

- 可交换性：主要混杂因素已被充分观测并纳入 `X`
- 重叠性：各类受试者都有接受不同处理的可能
- 一致性：`T` 的定义清晰、实际处理与定义一致
- SUTVA：个体之间不存在显著处理干扰

当前限制：

- 仍为演示级原型，不是正式因果研究平台
- 结局值目前可由文本中提取，仍依赖输入规范
- 若本地未安装真实因果依赖，会使用占位估计器
- 仅供科研分析，不替代临床诊疗

## 如何从规则引擎平滑替换为真实模型引擎

### 推荐引擎替换路径

当前规则引擎通过以下结构实现：

- 配置：`backend/app/config_data/recommendation_rules.json`
- 服务：`backend/app/services/recommendation_service.py`
- 结果落库：`prediction_results`
- 版本管理：`model_versions`

后续如果接入真实预测模型，可保持以下接口稳定：

1. 保持 `/api/v1/recommendations/*` 路由不变
2. 将 `recommendation_service.py` 中的规则打分替换为模型推理
3. 在 `model_versions` 中新增或激活 `predictive` 类型版本
4. 继续把输出写回 `prediction_results`

### 因果模型替换路径

当前因果模式通过以下结构实现：

- 数据读取：`backend/app/modeling/data_reader.py`
- 特征选择：`backend/app/modeling/feature_selection.py`
- 拆分：`backend/app/modeling/splitter.py`
- 估计器接口：`backend/app/modeling/estimators.py`
- 模型中心服务：`backend/app/services/model_center_service.py`

后续如接入真实因果模型，可按以下方式替换：

1. 在 `backend/app/modeling/estimators.py` 中增加真实估计器适配器
2. 让 `build_causal_estimator()` 优先返回真实实现
3. 保持 `/api/v1/model-center/*` 接口不变
4. 继续将版本信息写入 `model_versions`
5. 继续将训练产物写入 `backend/app/model_artifacts/`

这样前端“模型中心”和“因果评估结果”页面无需改动。

## 页面截图占位说明

如需为论文、答辩或软著准备截图，可使用以下占位路径：

1. `docs/screenshots/01-login.png`
2. `docs/screenshots/02-dashboard.png`
3. `docs/screenshots/03-data-center.png`
4. `docs/screenshots/04-subject-list.png`
5. `docs/screenshots/05-subject-detail.png`
6. `docs/screenshots/06-baseline-form.png`
7. `docs/screenshots/07-questionnaire-form.png`
8. `docs/screenshots/08-sleep-form.png`
9. `docs/screenshots/09-light-form.png`
10. `docs/screenshots/10-followup-form.png`
11. `docs/screenshots/11-data-quality.png`
12. `docs/screenshots/12-recommendation-center.png`
13. `docs/screenshots/13-report-center.png`
14. `docs/screenshots/14-model-center.png`
15. `docs/screenshots/15-causal-results.png`
16. `docs/screenshots/16-system-settings.png`

## 已完成

- 单仓库项目骨架
- 10 张核心表
- 数据库初始化与 100 例模拟数据脚本
- 患者 CRUD 与导入接口
- 数据中心与结构化数据质量页面
- 受试者管理与分项录入页面
- 规则/评分版推荐引擎
- 推荐报告预览与导出
- 模型中心版本管理、参数复用与版本对比
- 因果获益评估演示流程与复现性元数据
- 后端 Pytest、前端 Vitest、GitHub Actions CI

## 当前未完成

- 正式用户权限体系
- 真正的临床级预测模型与因果估计器
- 多次随访、多版本量表的复杂时序管理
- HIS 对接、设备实时接入、移动端
