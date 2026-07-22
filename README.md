# AI Daily

> 每日自动聚合 AI 新闻、学术论文与热点趋势，生成静态 HTML 页面并发布微信公众号草稿。

[English](./README_EN.md) | 中文

---

## 项目概览

AI Daily 是一套全自动的内容聚合管线，每日定时抓取多个数据源，经去重、过滤、翻译后生成三个独立的静态 HTML 页面，并可选发布到微信公众号草稿箱。所有流程由 GitHub Actions 定时触发，无需服务器。

### 三条管线 + 一个发布通道

| 模块 | 入口脚本 | 数据源 | 输出 | 定时（北京时间） |
|---|---|---|---|---|
| **AI 日报** | `generate_daily.py` | AI HOT + NewsNow（备用） | `daily_news.html` | 07:15 |
| **AI 论文** | `generate_papers.py` | AI HOT + arXiv + HuggingFace | `papers.html` | 07:15 |
| **趋势雷达** | `generate_trending.py` | NewsNow 多源（微博、头条、金十、财联社、华尔街见闻、参考消息、联合早报、澎湃） | `trending.html` | 07:00 / 13:00 |
| **微信草稿** | `generate_wechat.py` | 复用日报 + 论文的去重数据 | 微信公众号草稿 | 07:15 |

### 在线预览

👉 **[https://miaohua1982.github.io/ai-daily/](https://miaohua1982.github.io/ai-daily/)**

---

## 核心特性

- **多源聚合**：AI HOT API、arXiv、HuggingFace Daily Papers、NewsNow 多源热榜
- **智能去重**：URL 去重 + Embedding 语义去重（余弦相似度，可配阈值）
- **AI 过滤**：大模型对新闻标题打分筛选（DeepSeek），按兴趣领域分组
- **自动翻译**：arXiv / HuggingFace 英文论文自动翻译为中文（DeepSeek）
- **微信发布**：自动生成封面图 + 草稿，推送 Server 酱通知
- **历史归档**：每日生成归档文件，首页自动展示历史列表
- **管线抽象**：三条管线统一继承 `GeneratorPipeline`，接口一致、可扩展

---

## 架构设计

```
GeneratorPipeline (抽象基类, src/pipeline.py)
  ├── fetch_data()      # 抽象 — 子类实现
  ├── dedup_data()      # 默认 — 调用 utils.dedup_data（URL + 语义）
  ├── filter_data()     # 默认透传 — trending 覆盖
  ├── generate_html()   # 抽象 — 子类实现
  ├── write_files()     # 默认 — 写入 index + archive
  ├── git_commit()      # 默认 — git add + commit + push
  └── run()             # 模板方法 — 编排上述六步
      │
      ├── NewsPipeline       (src/news/pipeline.py)
      ├── PapersPipeline     (src/papers/pipeline.py)
      └── TrendingPipeline   (src/trending/pipeline.py)  ← 覆盖 filter_data + date_str
```

### 目录结构

```
ai-daily/
├── generate_daily.py          # AI 日报入口
├── generate_papers.py         # AI 论文入口
├── generate_trending.py       # 趋势雷达入口
├── generate_wechat.py         # 微信草稿发布入口
├── index.html                 # 首页（导航 + 历史归档）
├── archive/                    # 运行产物：历史归档（news / papers / trending / wechat_draft）
│
├── src/
│   ├── pipeline.py            # GeneratorPipeline 抽象基类
│   ├── news/                  # 新闻管线
│   │   ├── pipeline.py        #   NewsPipeline
│   │   ├── fetcher.py         #   数据获取（aihot + newsnow）
│   │   ├── renderer.py        #   HTML 渲染
│   │   └── constants.py       #   分类常量
│   ├── papers/                # 论文管线
│   │   ├── pipeline.py        #   PapersPipeline
│   │   ├── fetcher.py         #   多源获取 + 英文翻译
│   │   ├── renderer.py        #   HTML 渲染
│   │   └── constants.py       #   数据源颜色
│   ├── trending/              # 趋势雷达管线
│   │   ├── pipeline.py        #   TrendingPipeline
│   │   ├── fetcher.py         #   NewsNow 多源抓取
│   │   ├── filter.py          #   关键词 / AI 过滤 + 分组
│   │   └── renderer.py        #   HTML 渲染
│   └── wechat/                # 微信发布
│       ├── fetcher.py         #   复用 news/papers 的 fetch + dedup
│       ├── renderer.py        #   微信草稿 HTML 渲染
│       ├── cover.py           #   封面图生成（Pillow）
│       └── api.py             #   微信 API 客户端
│
├── utils/
│   ├── utils.py               # 共享工具（dedup / write_files / git_commit / get_now_date_str）
│   └── html_template.py       # HTML 模板（CSS / 卡片 / 布局）
│
├── config/
│   ├── news_config.yaml       # 日报配置
│   ├── papers_config.yaml     # 论文配置
│   ├── trending_config.yaml   # 趋势雷达配置
│   └── wechat_config.yaml     # 微信发布配置
│
├── .github/workflows/
│   ├── daily.yml              # 日报 — 每天 07:15
│   ├── papers.yml             # 论文 — 每天 07:15
│   ├── trending.yml           # 趋势 — 每天 07:00 / 13:00
│   └── wechat.yml             # 微信 — 每天 07:15
│
├── test/
│   ├── test.py                # 三管线集成测试（stub 模式 + --live 模式）
│   └── test_cover.py          # 封面图测试
│
├── requirements.txt           # Python 依赖
└── .env                       # 本地环境变量（不入库）
```

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/miaohua1982/ai-daily.git
cd ai-daily
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

> 微信封面图生成需要额外安装 Pillow：`pip install Pillow`

### 3. 配置环境变量

创建 `.env` 文件（或通过 GitHub Secrets 配置）：

```bash
# 语义去重（Embedding API）— 阿里云 DashScope 兼容模式
EMBEDDING_API_KEY=your_embedding_api_key

# AI 过滤 + 论文翻译（DeepSeek）
DEEPSEEK_API_KEY=your_deepseek_api_key

# 微信公众号发布（仅 generate_wechat.py 需要）
WECHAT_APPID=your_wechat_appid
WECHAT_APPSECRET=your_wechat_appsecret
```

### 4. 本地运行

```bash
# 生成 AI 日报
python generate_daily.py

# 生成 AI 论文
python generate_papers.py

# 生成趋势雷达
python generate_trending.py

# 发布微信草稿（需配置微信凭证）
python generate_wechat.py
```

### 5. 运行测试

```bash
# Stub 模式（快速，不调用真实 API）
python test/test.py

# Live 模式（调用真实 API，可能较慢）
python test/test.py --live
```

测试输出写入 `craft/` 目录（已被 `.gitignore` 忽略）。

---

## 配置说明

每条管线有独立的 YAML 配置文件，位于 `config/` 目录。

### 关键配置项

| 配置 | 文件 | 说明 |
|---|---|---|
| 数据源 API 地址 | 各 `*_config.yaml` | aihot / arXiv / HuggingFace / NewsNow |
| 语义去重 | 各 `*_config.yaml` → `semantic_dedup` | `enabled` / `threshold` / `api_key_env` / `model` |
| AI 过滤 | `trending_config.yaml` → `filter` + `ai` | `method: keyword\|ai\|both` / `min_score` / `interests` |
| 关键词分组 | `trending_config.yaml` → `keywords` | 按领域分组（AI大模型 / 智能汽车 / 机器人 / 财经 / 国际） |
| 论文翻译 | `papers_config.yaml` → `translation` | `enabled` / `batch_size` / `model` |
| 微信发布 | `wechat_config.yaml` | 标题模板 / 摘要模板 / 内容截断上限 |

### 语义去重配置示例

```yaml
semantic_dedup:
  enabled: true
  api_key_env: "EMBEDDING_API_KEY"
  base_url: "https://llm-860ckp050tycaw8n.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
  model: "text-embedding-v4"
  threshold: 0.85       # 余弦相似度 >= 此值视为重复
  batch_size: 10
```

---

## GitHub Actions 部署

项目通过 GitHub Actions 定时运行，无需自建服务器。

### 需要配置的 Secrets

在仓库 **Settings → Secrets and variables → Actions** 中添加：

| Secret | 用途 | 必需 |
|---|---|---|
| `EMBEDDING_API_KEY` | 语义去重 Embedding API | 启用语义去重时必需 |
| `DEEPSEEK_API_KEY` | AI 过滤 + 论文翻译 | 启用 AI 过滤 / 翻译时必需 |
| `WECHAT_APPID` | 微信公众号 AppID | 仅微信发布需要 |
| `WECHAT_APPSECRET` | 微信公众号 AppSecret | 仅微信发布需要 |
| `SERVERCHAN_SENDKEY` | Server 酱通知密钥 | 可选，接收成功 / 失败通知 |

### Actions 定时计划

| Workflow | 北京时间 | UTC | 频率 |
|---|---|---|---|
| `daily.yml` | 07:15 | 23:15（前一天） | 每天 |
| `papers.yml` | 07:15 | 23:15（前一天） | 每天 |
| `trending.yml` | 07:00 / 13:00 | 23:00 / 05:00 | 每天 2 次 |
| `wechat.yml` | 07:15 | 23:15（前一天） | 每天 |

所有 Actions 均支持 `workflow_dispatch` 手动触发。

---

## 管线流程详解

### AI 日报（NewsPipeline）

```
aihot API ──→ fetch_data ──→ dedup_data ──→ generate_html ──→ write_files ──→ git_commit
newsnow API ─┘    (URL + 语义去重)          (分类渲染)        (index + archive)
```

- 主源 AI HOT，不可用时自动切换 NewsNow
- 每条新闻携带 `publishTime`，渲染时独立计算时间
- 按分类（AI / 产品 / 研究等）分组展示

### AI 论文（PapersPipeline）

```
aihot ──→ fetch_data ──→ translate ──→ dedup_data ──→ generate_html ──→ write_files ──→ git_commit
arXiv ──┤    (多源合并)   (英→中)       (URL + 语义)    (卡片渲染)
HF ─────┘
```

- 三源合并：AI HOT 论文频道 + arXiv 分类检索 + HuggingFace Daily Papers
- 英文标题 / 摘要自动翻译为中文（DeepSeek，批量翻译）
- 跨源去重（同一论文可能同时出现在 arXiv 和 HuggingFace）

### 趋势雷达（TrendingPipeline）

```
NewsNow ──→ fetch_data ──→ dedup_data ──→ filter_data ──→ generate_html ──→ write_files ──→ git_commit
(8 源)        (URL + 语义)   (关键词/AI)    (分组渲染)      (index + archive)
```

- 8 个数据源分 3 组：综合热榜 / 财经金融 / 国际深度
- AI 过滤：DeepSeek 对每条新闻打分（0-1），保留 ≥ `min_score` 的条目
- 按 5 个领域分组展示：国际局势 / 财经资讯 / AI大模型 / 智能汽车 / 机器人与具身智能
- 每日两次更新（07:00 / 13:00），归档文件名带小时后缀 `YYYY-MM-DD-HH`

### 微信草稿（generate_wechat.py）

```
gd.fetch_data ──→ gd.dedup_data ─┐
gp.fetch_data ──→ gp.dedup_data ─┤→ render_wechat_html → generate_cover → upload_image → create_draft
                                 │                       (Pillow 绘图)     (微信 API)      (草稿箱)
```

- 复用日报 + 论文的 fetch + dedup 步骤，截取前 N 条
- Pillow 自动生成封面图（日期 + 条数统计）
- 通过微信公众号 API 创建草稿，不自动发布
- 成功 / 失败均通过 Server 酱推送通知

---

## 技术栈

| 层面 | 技术 |
|---|---|
| 语言 | Python 3.13 |
| 依赖 | PyYAML（唯一硬依赖）、Pillow（微信封面图，可选） |
| CI/CD | GitHub Actions |
| AI 服务 | DeepSeek（过滤 + 翻译）、阿里云 DashScope（Embedding 语义去重） |
| 数据源 | AI HOT API、arXiv API、HuggingFace API、NewsNow API |
| 微信 | 微信公众号开放平台 API |
| 通知 | Server 酱 |

---

## 扩展开发

### 新增一条管线

1. 创建 `src/<name>/` 目录，包含 `pipeline.py`、`fetcher.py`、`renderer.py`
2. 继承 `GeneratorPipeline`，实现 `fetch_data` 和 `generate_html`
3. 如需过滤步骤，覆盖 `filter_data`
4. 创建 `generate_<name>.py` 入口脚本
5. 创建 `config/<name>_config.yaml` 配置文件
6. 添加 `.github/workflows/<name>.yml` 定时任务

```python
from src.pipeline import GeneratorPipeline

class MyPipeline(GeneratorPipeline):
    OUTPUT_DIR  = Path(__file__).parent.parent.parent
    ARCHIVE_DIR = OUTPUT_DIR / "archive" / "my"
    INDEX_FILE  = OUTPUT_DIR / "my.html"
    CONFIG_FILE = OUTPUT_DIR / "config" / "my_config.yaml"

    def fetch_data(self, config):
        return _fetch_impl(config)

    def generate_html(self, items):
        return _render_impl(items)
```

只需实现两个抽象方法，`dedup_data`、`write_files`、`git_commit`、`run` 全部继承基类。

---

## License

MIT
