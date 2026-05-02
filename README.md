# 📚 智能文档处理系统

> 基于 Flask + Vue 3 的企业级中文文档智能处理平台，支持文档解析、文本预处理、信息抽取、关键词与抽取式摘要生成、批量处理与多格式导出。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4+-brightgreen.svg)](https://vuejs.org/)
[![Element Plus](https://img.shields.io/badge/Element%20Plus-2.9-409EFF.svg)](https://element-plus.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ 项目简介

**智能文档处理系统** 是一套面向中文文本场景的全栈式文档智能处理平台。系统支持 TXT / DOCX / PDF 等多格式文档的批量上传与解析，提供细粒度可配置的文本预处理流程，基于 TF-IDF / TextRank 的关键词提取与**真正的句子级抽取式摘要**，并通过规则与算法双引擎完成结构化信息抽取。

系统采用前后端分离架构，后端基于 Flask + SQLAlchemy + 多线程 ThreadPoolExecutor 实现高吞吐文档处理，前端基于 Vue 3 + Element Plus + Pinia 构建现代化交互界面，结果支持 JSON / Excel / CSV 多格式导出，并提供完整的 RBAC 权限控制与审计日志。

---

## 🚀 核心功能

### 📄 文档导入与解析
- 支持 **TXT、DOCX、PDF** 等主流格式（自动 UTF-8 / GBK 编码检测）
- 拖拽上传、批量上传、单文件最大 50 MB
- 文档元信息管理（文件类型、大小、状态、上传时间）

### 🧹 文本预处理（高度可配置 + 处理过程可视化）
- **分词纠错**：基于可扩展词典 (`typo_dict.txt`) 的中文错词纠正
- **噪声过滤**：自动检测并移除页眉、页脚、页码、乱码、特殊符号、URL/HTML 标签
- **去重清洗**：基于 Jaccard 相似度的段落去重
- **可选模块**：中文分词、停用词过滤、词性标注、正则匹配、字符规范化、短行过滤
- **🔄 处理过程时间线**：每一步都记录处理日志，前端可视化展示纠错明细与压缩比

### 🔑 关键词与抽取式摘要
- **关键词提取**：TF-IDF / TextRank 双算法可选，输出 Top-K 权重词
- **TextRank 句子级抽取式摘要**：
  - 真正的句子级 TextRank 实现（相似度矩阵 + 阻尼系数迭代收敛）
  - 自动过滤页眉页脚和重复段落
  - 严格匹配用户配置的目标摘要长度（±10% 区间内）
  - **🎯 句子打分可视化**：前端高亮被 TextRank 选中的句子，并展示每句重要性分数

### 🔍 信息抽取
- **规则抽取**：日期、金额、邮箱、电话号码（正则模式匹配）
- **算法抽取**：人名、机构名、地点（基于 jieba 词性标注）
- **置信度评分**：每条抽取结果附带置信度
- 支持单文档抽取与未解析文档的自动解析

### ⚡ 多线程批量处理
- 基于 `ThreadPoolExecutor` 的并发处理（可配置线程数 1–8）
- 支持单次提交多文档、多类型任务（解析 + 预处理 + 抽取 + 摘要）
- 主线程统一写库，子线程纯函数式处理，**线程安全**
- 完整的成功 / 失败反馈与错误回溯

### 📊 结果可视化与多格式导出
- **结构化展示**：所有结果直接铺开展示，关键词云、摘要打分、抽取表格、预处理统计一目了然
- **交互式查看**：搜索、按文档/类型筛选、卡片视图与紧凑视图切换
- **多格式导出**：JSON / Excel (.xlsx) / CSV，每个结果独立导出按钮

### 👥 用户与权限管理
- **双角色 RBAC**：管理员 (admin) / 普通用户 (user)
- 管理员独享：用户管理、操作日志查看
- 路由级 + 接口级双重权限拦截，普通用户无法绕过 URL 直接访问受限页面
- 账号禁用机制（`status=0` 立即生效）

### 📋 操作日志（审计）
- 全量记录用户行为：登录、退出、注册、改密、上传、解析、删除、预处理、抽取、摘要、批量处理、导出、用户管理
- 自动记录 IP 地址（含 X-Forwarded-For 支持）
- 仅管理员可查看，支持按用户名 / 操作类型筛选

---

## 🏗️ 技术架构

### 后端（Python）
| 类别 | 技术栈 |
| --- | --- |
| Web 框架 | Flask 2.3+ |
| ORM | SQLAlchemy + Flask-Migrate |
| 数据库 | MySQL 8.0+（utf8mb4） |
| 跨域 | Flask-CORS |
| 文档解析 | python-docx · pdfplumber |
| NLP | jieba · scikit-learn (TF-IDF) |
| 并发 | concurrent.futures.ThreadPoolExecutor |
| 数据处理 | pandas · openpyxl |

### 前端（TypeScript）
| 类别 | 技术栈 |
| --- | --- |
| 框架 | Vue 3.4 + TypeScript |
| 构建 | Vite 5 |
| UI | Element Plus 2.9 + UnoCSS |
| 状态管理 | Pinia + pinia-plugin-persistedstate |
| 路由 | Vue Router (基于文件的自动路由) |
| HTTP | Axios |
| 工具 | @vueuse/core · NProgress |

### 数据模型
```
User ──┬── Token
       ├── OperationLog
       ├── Document ──┬── ProcessTask ──┬── ExtractionResult
       │              │                 └── KeywordSummary
       └── ProcessTask
```

---

## 📦 项目结构

```
python-doc-processing/
├── app.py                    # 应用启动入口
├── .env                      # 后端环境变量配置
├── requirements.txt          # Python 依赖清单
├── uploads/                  # 文档上传目录（自动创建）
├── App/
│   ├── __init__.py           # Flask 应用工厂
│   ├── exts.py               # SQLAlchemy / Migrate / CORS 初始化
│   ├── models.py             # 数据模型定义
│   ├── views.py              # 路由 + 视图函数
│   └── utils/
│       ├── api_utils.py      # 统一响应封装
│       ├── document_parser.py# TXT / DOCX / PDF 解析
│       ├── config.py         # 系统配置管理
│       ├── stopwords.txt     # 停用词表
│       └── typo_dict.txt     # 错词词典（可扩展）
└── front/
    ├── index.html
    ├── package.json
    ├── .env                  # 前端环境变量
    ├── vite.config.ts
    └── src/
        ├── main.ts
        ├── App.vue
        ├── api/              # API 封装
        ├── components/       # 全局组件
        ├── composables/      # 通用 hooks
        ├── layouts/          # 布局组件
        ├── pages/            # 业务页面（自动路由）
        │   ├── index.vue                  # 首页
        │   ├── login.vue                  # 登录
        │   ├── register.vue               # 注册
        │   ├── document-import.vue        # 文档导入
        │   ├── text-preprocess.vue        # 文本预处理
        │   ├── information-extraction.vue # 信息抽取
        │   ├── keyword-summary.vue        # 关键词摘要
        │   ├── result-display.vue         # 结果展示
        │   ├── batch-processing.vue       # 批量处理
        │   ├── operation-log.vue          # 操作日志（仅管理员）
        │   └── user.vue                   # 用户管理（仅管理员）
        ├── plugins/          # Pinia / Router / NProgress 配置
        ├── stores/           # Pinia 状态
        ├── styles/           # 全局样式与主题
        └── utils/            # 工具函数
```

---

## 🛠️ 快速开始

### 环境要求

- **Python** 3.10 或更高
- **Node.js** 20.12.2 或更高
- **MySQL** 8.0 或更高
- **pnpm** 8.x（或 npm / yarn）

### 1️⃣ 克隆仓库

```bash
git clone https://github.com/<your-username>/python-doc-processing.git
cd python-doc-processing
```

### 2️⃣ 数据库准备

```sql
CREATE DATABASE doc_processing DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 3️⃣ 后端启动

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

在项目根目录创建 `.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=your_password
DB_DATABASE=doc_processing
DB_CHARSET=utf8mb4
```

执行数据库迁移：

```bash
flask --app app.py db init
flask --app app.py db migrate -m "init"
flask --app app.py db upgrade
```

启动后端：

```bash
python app.py
# 后端服务: http://localhost:5000
```

### 4️⃣ 创建初始管理员账号

在 Python 中生成密码哈希：

```python
import hashlib
print(hashlib.sha256('admin123'.encode()).hexdigest())
# 输出: 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
```

在 MySQL 中执行：

```sql
INSERT INTO tb_user (username, password, role, status, created_at)
VALUES ('admin',
        '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
        0, 1, NOW());
```

> `role=0` 为管理员，`role=1` 为普通用户。

### 5️⃣ 前端启动

```bash
cd front
pnpm install
```

创建 `front/.env`：

```env
VITE_APP_TITLE=文档处理系统
VITE_ADMIN_API_BASE_URL=http://localhost:5000
```

启动开发服务器：

```bash
pnpm dev
# 前端服务: http://localhost:5173
```

访问 `http://localhost:5173`，使用 `admin / admin123` 登录。

### 6️⃣ 生产构建（可选）

```bash
cd front
pnpm build
# 产物输出到 front/dist/，后端会自动 serve
```

构建后只需启动后端，访问 `http://localhost:5000` 即可使用整套系统。

---

## 📸 功能截图

> 在此处放置功能展示截图（建议放到 `docs/screenshots/` 目录下）

| 页面 | 描述 |
| --- | --- |
| 文档导入 | 拖拽上传、批量上传、解析、内容预览 |
| 文本预处理 | 多功能开关 + 处理过程时间线可视化 |
| 关键词摘要 | TextRank 句子打分可视化 |
| 结果展示 | 结构化卡片、多格式导出 |
| 批量处理 | 多线程并发进度展示 |
| 操作日志 | 全量审计日志（仅管理员） |

---

## 🎯 API 文档

### 认证相关

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/register` | 用户注册 |
| POST | `/api/login` | 登录获取 token |
| POST | `/api/logout` | 退出登录 |
| GET | `/sys/user/info` | 获取当前用户信息 |
| POST | `/change_password` | 修改密码 |

### 文档管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/document/upload` | 上传文档 |
| GET | `/api/document/list` | 文档列表（分页） |
| POST | `/api/document/<id>/parse` | 解析文档 |
| GET | `/api/document/<id>/content` | 获取文档内容 |
| DELETE | `/api/document/<id>` | 删除文档 |

### 文本处理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/text/preprocess` | 文本预处理（支持多文档） |
| POST | `/api/keyword-summary/generate` | 生成关键词与摘要 |
| POST | `/api/extraction/extract` | 信息抽取 |
| POST | `/api/batch/process` | 批量处理 |

### 结果与导出

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/results/all` | 聚合所有处理结果 |
| GET | `/api/task/<id>/result` | 获取单任务结果 |
| GET | `/api/task/<id>/export?format={json\|excel\|csv}` | 多格式导出 |

### 管理员功能

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/users/page` | 用户列表 |
| POST | `/api/users` | 新增用户 |
| PUT | `/api/users/<id>` | 修改用户 |
| DELETE | `/api/users/<id>` | 删除用户 |
| GET | `/api/operation-logs` | 操作日志查询 |
| GET | `/api/operation-logs/actions` | 操作类型枚举 |

> 所有非认证接口需在 Header 中携带 `token: <login_token>`

---

## 🧪 关键算法说明

### TextRank 句子级抽取式摘要

```
1. 文本预处理：移除页眉页脚 + 段落去重
2. 分句：按 。！？；!?; 切分（过滤过短/过长异常句）
3. 句子向量化：jieba 分词 → 词集合
4. 相似度矩阵：sim(i,j) = |Wi ∩ Wj| / (log|Wi| + log|Wj|)
5. PageRank 迭代：S(Vi) = (1-d) + d × Σ [sim(j,i) / Σsim(j,k)] × S(Vj)
6. 选句策略：按分数降序，达到目标长度 [-10%, +10%] 区间内停止
7. 还原顺序：按原文位置排序后拼接
```

阻尼系数 `d=0.85`，迭代次数 `30`，收敛速度快、效果稳定。

### 文本预处理流水线

```
原文 
  → ① 页眉页脚检测（基于行频统计）
  → ② URL/HTML 清理（可选）
  → ③ 全角→半角规范化（可选）
  → ④ 乱码 / 特殊符号过滤
  → ⑤ 段落 Jaccard 去重
  → ⑥ 短行过滤（可选）
  → ⑦ 错词词典纠错
  → ⑧ jieba 中文分词
  → ⑨ 停用词过滤
  → ⑩ 词性标注（可选）
  → ⑪ 正则匹配（可选）
```

---

## 🔧 配置说明

### 错词词典扩展

`App/utils/typo_dict.txt`，每行格式：

```
错词<TAB>正词
```

示例：

```
帐号	账号
迫不急待	迫不及待
```

支持 `#` 开头的注释行与空行，用户可自由扩展。

### 停用词扩展

`App/utils/stopwords.txt`，每行一个停用词。

### 上传限制调整

`App/views.py`：

```python
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
```

---

## 🛣️ Roadmap

- [ ] 集成更强大的 NLP 模型（如 LAC、HanLP）
- [ ] 支持更多文档格式（HTML、Markdown、EPUB）
- [ ] 异步任务队列（Celery + Redis）
- [ ] WebSocket 实时进度推送
- [ ] 文档版本管理与历史快照
- [ ] 多租户支持
- [ ] Docker 一键部署
- [ ] 国际化（i18n）
- [ ] 全文搜索（Elasticsearch）

---

## 🤝 贡献指南

欢迎任何形式的贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'feat: add AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 提交信息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/)：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档变更
- `style:` 代码格式（不影响功能）
- `refactor:` 重构
- `perf:` 性能优化
- `test:` 测试相关
- `chore:` 构建 / 工具链

### Bug 反馈与功能建议

欢迎在 [Issues](https://github.com/<your-username>/python-doc-processing/issues) 中提交。提交时请尽量提供：

- 复现步骤
- 期望行为 vs 实际行为
- 运行环境（Python / Node 版本、操作系统）
- 相关日志或截图

---

## 📄 开源协议

本项目基于 **MIT License** 开源，详见 [LICENSE](./LICENSE) 文件。

```
MIT License

Copyright (c) 2025 <your-name>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, ...
```

---

## 🙏 致谢

本项目使用了以下优秀的开源项目，特此致谢：

- [Flask](https://flask.palletsprojects.com/) - 轻量级 Python Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL 工具包
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - 基于 Vue 3 的桌面端组件库
- [jieba](https://github.com/fxsjy/jieba) - 中文分词组件
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF 解析库
- [scikit-learn](https://scikit-learn.org/) - 机器学习库

---

## 📮 联系方式

- 作者：<your-name>
- 邮箱：<your-email@example.com>
- GitHub：[@your-username](https://github.com/<your-username>)

如果这个项目对你有帮助，欢迎点一个 ⭐ Star 支持一下！

---

<p align="center">Made with ❤️ for Chinese NLP community</p>
