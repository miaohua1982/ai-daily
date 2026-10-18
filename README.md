# AI Daily

<!-- 【文档同步标识｜2026-10-18】同步新接口迁移、来源异常隔离、译文 ID 对齐、自然周过滤和离线白盒测试；未修改运行代码或定时配置。 -->

> 每日自动聚合 AI 新闻、学术论文与热点趋势，生成静态 HTML 页面并发布微信公众号草稿。

[English](./README_EN.md) | 中文

---

## 项目概览

AI Daily 是一套全自动的内容聚合管线，每日定时抓取多个数据源，经去重、过滤、翻译后生成三个独立的静态 HTML 页面，并可选发布到微信公众号草稿箱。所有流程由 GitHub Actions 定时触发，无需服务器。

### 三条管线 + 一个发布通道

| 模块 | 入口脚本 | 数据源 | 输出 | 定时（北京时间） |
|---|---|---|---|---|
| **AI 日报** | `generate_daily.py` | AI HOT + NewsNow（备用） | `daily_news.html` | 07:15 |
| **AI 论文** | `generate_papers.py` | AI HOT 优先；arXiv + HuggingFace 备用 | `papers.html` | 07:15 |
| **趋势雷达** | `generate_trending.py` | NewsNow 多源（微博、头条、金十、财联社、华尔街见闻、参考消息、联合早报、澎湃） | `trending.html` | 07:00 / 13:00 |
| **微信草稿** | `generate_wechat.py` | 复用新闻/论文抓取，跨区统一去重 | 微信公众号草稿 | 07:15 |
| **论文周报** | `generate_wechat_papers_weekly.py` | HuggingFace + arXiv；北京时间自然周 | 周报 HTML / Markdown、微信草稿 | 周日 17:00 |

### 在线预览

👉 **[https://miaohua1982.github.io/ai-daily/](https://miaohua1982.github.io/ai-daily/)**

---

## 核心特性

- **多源聚合**：AI HOT API、arXiv、HuggingFace Daily Papers、NewsNow 多源热榜
- **智能去重**：URL 去重 + Embedding 语义去重（余弦相似度，可配阈值）
- **AI 过滤**：大模型对新闻标题打分筛选（DeepSeek），按兴趣领域分组
- **自动翻译**：arXiv / HuggingFace 英文论文自动翻译为中文（DeepSeek），按批次内 ID 精确匹配，漏译保留原文
- **备用源隔离**：arXiv 与 HuggingFace 分别处理异常，一个失败不阻断另一个
- **自然周精选**：论文周报按北京时间过滤本周一零点至运行日结束的数据
- **微信发布**：自动生成封面图 + 草稿，推送 Server 酱通知
- **历史归档**：每日生成归档文件，首页自动展示历史列表
- **管线抽象**：三条管线统一继承 `GeneratorPipeline`，接口一致、可扩展

---

## 架构设计

```
GeneratorPipeline (抽象基类, src/pipeline.py)
  ├── fetch_data()      # 抽象 — 子类实现
  ├── dedup_data()      # 默认 — 调用 utils.dedup_data（URL + 语义）
  ├── filter_data()     # 默认透传 — news/papers 按摘要长度过滤，trending 按兴趣过滤
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
├── generate_wechat_papers_weekly.py # 论文周报入口
├── generate_wechat_video.py   # 已有视频上传为永久素材
├── index.html                 # 首页（导航 + 历史归档）
├── archive/                    # 运行产物：历史归档（news / papers / trending / wechat_draft / wechat_papers_weekly）
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
│       ├── fetcher.py         #   复用抓取/过滤 + 新闻论文统一去重
│       ├── weekly_fetcher.py  #   北京时间自然周过滤 + 排序精选
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
│   ├── wechat_config.yaml     # 微信日报发布配置
│   └── weekly_config.yaml     # 论文周报独立配置
│
├── .github/workflows/
│   ├── daily.yml              # 日报 — 每天 07:15
│   ├── papers.yml             # 论文 — 每天 07:15
│   ├── trending.yml           # 趋势 — 每天 07:00 / 13:00
│   ├── wechat.yml             # 微信 — 每天 07:15
│   └── wechat_papers_weekly.yml # 周报 — 周日 17:00
│
├── test/
│   ├── test.py                # pytest 统一离线入口
│   ├── conftest.py            # 网络/子进程/凭证隔离和公共样本
│   ├── test_cover.py          # PNG 与字体回退测试
│   ├── test_translation_alignment.py # 翻译 ID 对齐回归
│   ├── test_weekly_window.py  # 自然周与时区边界回归
│   ├── test_known_defects.py  # 已知缺陷与已修复回归
│   └── README.md              # 完整测试清单和命令
│
├── requirements.txt           # Python 运行依赖
├── requirements-test.txt      # 独立测试依赖
├── pytest.ini                 # 测试发现规则
├── .coveragerc                # Python 行/分支覆盖率配置
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

# 仅生成本地预览（wechat.md / wechat.html，不调用微信 API、无需微信凭证）
WECHAT_LOCAL_ONLY=1 python generate_wechat.py
# 或用命令行参数：python generate_wechat.py --local-only

# 生成并发布周报草稿（需配置微信凭证）
python generate_wechat_papers_weekly.py
# 仅生成本地预览（wechat_papers_weekly.md / .html，不调用微信 API、无需微信凭证）
WECHAT_LOCAL_ONLY=1 python generate_wechat_papers_weekly.py
# 或用命令行参数：python generate_wechat_papers_weekly.py --local-only
```

### 5. 运行测试

<!-- 【测试说明更新｜2026-10-18】替换旧 stub/--live 脚本用法，明确隔离范围与已知失败。 -->
```bash
python -m pip install -r requirements-test.txt
python -B -m pytest -q
# 兼容原入口（同样运行离线测试）
python -B test/test.py

# Python 行/分支覆盖率报告
mkdir -p craft/coverage
python -B -m coverage run -m pytest -q
python -B -m coverage report
python -B -m coverage html -d craft/coverage/html
python -B -m coverage json -o craft/coverage/coverage.json
```

在本机使用已有环境时，将 `python` 换成 `../venv/bin/python`。测试禁止未模拟的网络、socket 和子进程，隔离真实 API 凭证；生成物只写入测试临时目录，覆盖率报告位于已忽略的 `craft/coverage/`。旧 `--live` 测试模式已移除；生产脚本的真实抓取不属于这套离线测试。

2026-10-18 的验证快照：**310 项测试，307 passed，3 strict xfailed；Python 行覆盖率 99.77%，分支覆盖率 99.37%**。预期失败代表尚未修复的问题，不计为通过；数字随后续代码变化，以重新运行结果为准。Python 覆盖率不包含 HTML 内 JavaScript 或 GitHub Actions 的运行行为，也不等于所有输入/循环路径覆盖。

目前仍保留三项缺陷回归：无 PyYAML 时简易解析器的空列表项、管线 Git 归档路径缺少 `archive/`、论文 JSON 嵌入脚本时未转义 `</script>`。翻译 ID 错配和周报自然周问题已修复，对应用例必须正常通过。

完整说明见 [test/README.md](test/README.md)，可用 `python -B -m pytest test/test_known_defects.py --runxfail -q` 查看剩余缺陷的真实失败（预期非零退出）。

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

### AIHOT v1 接口迁移

<!-- 【接口迁移说明｜2026-10-18】与 config 和两条抓取管线的实际适配保持一致。 -->
新闻、论文以及周报中已关闭的 AI HOT 配置均统一使用 `https://aihot.news/api/v1`。旧 `/api/public/*` 的官方停服日期为 2026-10-31；迁移依据见 [AIHOT 官方指南](https://aihot.news/agent?tab=api#legacy-api-migration)。

| 项目调用 | v1 适配方式 |
|---|---|
| 指定日期 / 最新日报 | `/dailies/{date}` / `/dailies/latest`，读取 `report.sections` |
| 论文列表 | `/items?mode=all&category=paper&window=7d&by=published&limit=...` |
| 数量和日期 | 本地配置 `take` 保留，发请求时改为 `limit`；用 `window=7d` 后按原 `days_back` 本地过滤 |
| 分页 | 读取 `page.hasMore` / `page.nextCursor`，cursor 编码后传递，每次运行从首屏开始 |
| 原文 / 来源 | `links.original`、`source.name` 转换为现有内部字段，兼容网页、去重和微信渲染 |

只适配日报正文，暂未将 `flashes` 快讯纳入现有摘要过滤。列表仅提供滚动近 7 天，配置更早的日期不能据此补取历史数据。现有 workflow 定时配置保持原样。

### 语义去重配置示例

```yaml
semantic_dedup:
  enabled: true
  api_key_env: "EMBEDDING_API_KEY"
  base_url: "https://llm-860ckp050tycaw8n.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
  model: "text-embedding-v4"
  threshold: 0.75       # 余弦相似度 >= 此值视为重复
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
| `wechat_papers_weekly.yml` | 周日 17:00 | 周日 09:00 | 每周 |

上表是 workflow 中的配置时间，实际启动可能延迟；本次未调整定时配置。所有 Actions 均支持 `workflow_dispatch` 手动触发。

---

## 管线流程详解

### AI 日报（NewsPipeline）

```
AIHOT 指定日期日报 → 最新日报 → NewsNow（沿用原回退顺序）
  → 字段适配 → URL/语义去重 → 摘要长度过滤 → HTML → 文件/归档 → Git
```

- v1 从 `report.sections` 读取正文，转换链接、来源与分类为现有字段。
- 每条新闻沿用 `publishTime`，按分类展示；摘要下限由 `filter.min_summary_len` 控制。

### AI 论文（PapersPipeline）

```
AIHOT 有数据 → 直接使用
AIHOT 无数据 → arXiv + HuggingFace（独立捕获异常）→ 合并 → 英文翻译
  → URL/语义去重 → 摘要长度过滤 → HTML → 文件/归档 → Git
```

- 并非每次合并三源：AI HOT 返回论文时，跳过 arXiv / HuggingFace；备用源一个失败时仍尝试另一个，保留成功结果。
- 【译文对齐修复】按每批从 0 开始的整数 ID 匹配，不再按位置 `zip`；缺项保留原文。无 ID、非法或越界 ID 被忽略，重复 ID 保留首次结果并告警。
- 标题和摘要字段分别校验类型，异常字段保留原文，空译文不计入成功数；跨批次重新编号，避免错配。
- 去重和渲染继续使用现有内部数据结构。

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
新闻/论文抓取 + 摘要过滤 → 合并做 URL/语义去重（新闻优先）→ 各区块截取前 N 条
  → 本地 HTML / Markdown 与归档
  → 非 local-only 时：封面 → 上传 → 创建微信草稿
```

- 默认最多 10 条新闻和 10 篇论文；本地模式也会抓取和去重，但不上传封面或创建草稿。
- Pillow 生成封面；微信 API 只创建草稿，不自动正式发表。成功/失败通知由 workflow 调用 Server 酱。

### 论文周报（generate_wechat_papers_weekly.py）

<!-- 【自然周修复说明｜2026-10-18】抓取天数与日期差分开，普通论文页滚动过滤不变。 -->
- 直接抓取 HuggingFace + arXiv，跳过 AI HOT；两源分别捕获异常。
- HF 仍逐天请求周一至运行日；合并后按北京时间严格保留 **本周一 00:00（含）至运行日次日 00:00（不含）** 的 `publishedAt`。
- UTC/Z 和带偏移时间会转为北京时间；无偏移时间按 UTC 解释，缺失或无法解析的时间剔除。
- 例如周日 2026-10-18 运行，保留北京时间 10-12 至 10-18 的论文；上周日不再混入，UTC 10-11 16:00 等于北京时间周一零点，仍应保留。
- 之后做摘要过滤、去重、排序（HF 热度优先）、截断 `top_n`（默认 30）再翻译，生成 HTML / Markdown 和可选微信草稿。普通论文页的共享日期过滤未改。

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
