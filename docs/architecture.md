# 架构说明

## 目标定位

当前版本用于科研演示和原型搭建，强调以下目标：

- 快速启动
- 易于扩展
- 前后端分离
- 本地与 Docker 双模式运行

## 技术栈

- 后端：FastAPI + SQLAlchemy + Pydantic + SQLite
- 前端：Vue3 + Vite + TypeScript + Element Plus + Pinia + Vue Router + ECharts
- 编排：Docker Compose

## 分层设计

- 前端负责登录演示、管理台壳与 Dashboard 展示。
- 后端提供基础接口、配置管理和 SQLite 持久化。
- 数据层当前仅保留演示用户表，后续可扩展病例、评估、推荐等实体。

## 当前边界

- 仅供科研辅助，不替代临床诊断与治疗。
- 不做真实 HIS 对接。
- 不做设备实时接入。
- 不做移动端。
