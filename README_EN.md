# AI Daily

> Automatically aggregate AI news, academic papers, and trending topics daily into static HTML pages and WeChat Official Account drafts.

English | [中文](./README.md)

---

## Overview

AI Daily is a fully automated content aggregation pipeline that fetches from multiple data sources on a daily schedule, deduplicates, filters, and translates the content, then generates three independent static HTML pages with an optional WeChat draft publish step. All workflows are triggered by GitHub Actions — no server required.

### Three Pipelines + One Publishing Channel

| Module | Entry Script | Data Sources | Output | Schedule (Beijing Time) |
|---|---|---|---|---|
| **AI News** | `generate_daily.py` | AI HOT + NewsNow (fallback) | `daily_news.html` | 07:15 |
| **AI Papers** | `generate_papers.py` | AI HOT + arXiv + HuggingFace | `papers.html` | 07:15 |
| **Trending Radar** | `generate_trending.py` | NewsNow multi-source (Weibo, Toutiao, Jin10, CLS, Wallstreetcn, Cankaoxiaoxi, Zaobao, Thepaper) | `trending.html` | 07:00 / 13:00 |
| **WeChat Draft** | `generate_wechat.py` | Reuses news + papers deduped data | WeChat Official Account draft | 07:15 |

### Live Preview

👉 **[https://miaohua1982.github.io/ai-daily/](https://miaohua1982.github.io/ai-daily/)**

---

## Key Features

- **Multi-source aggregation**: AI HOT API, arXiv, HuggingFace Daily Papers, NewsNow trending feeds
- **Smart deduplication**: URL dedup + embedding-based semantic dedup (cosine similarity, configurable threshold)
- **AI filtering**: LLM scoring on news headlines (DeepSeek), grouped by interest domains
- **Auto translation**: arXiv / HuggingFace English papers automatically translated to Chinese (DeepSeek)
- **WeChat publishing**: Auto-generated cover image + draft creation, with ServerChan notifications
- **Historical archive**: Daily archive files generated automatically; index page lists history
- **Pipeline abstraction**: Three pipelines unified under `GeneratorPipeline` — consistent interface, easily extensible

---

## Architecture

```
GeneratorPipeline (abstract base class, src/pipeline.py)
  ├── fetch_data()      # abstract — implemented by subclass
  ├── dedup_data()      # default — calls utils.dedup_data (URL + semantic)
  ├── filter_data()     # default passthrough — overridden by trending
  ├── generate_html()   # abstract — implemented by subclass
  ├── write_files()     # default — writes index + archive
  ├── git_commit()      # default — git add + commit + push
  └── run()             # template method — orchestrates all six steps
      │
      ├── NewsPipeline       (src/news/pipeline.py)
      ├── PapersPipeline     (src/papers/pipeline.py)
      └── TrendingPipeline   (src/trending/pipeline.py)  ← overrides filter_data + date_str
```

### Directory Structure

```
ai-daily/
├── generate_daily.py          # AI News entry point
├── generate_papers.py         # AI Papers entry point
├── generate_trending.py       # Trending Radar entry point
├── generate_wechat.py         # WeChat draft publish entry point
├── index.html                 # Landing page (navigation + archive list)
│
├── src/
│   ├── pipeline.py            # GeneratorPipeline abstract base class
│   ├── news/                  # News pipeline
│   │   ├── pipeline.py        #   NewsPipeline
│   │   ├── fetcher.py         #   Data fetching (aihot + newsnow)
│   │   ├── renderer.py        #   HTML rendering
│   │   └── constants.py       #   Category constants
│   ├── papers/                # Papers pipeline
│   │   ├── pipeline.py        #   PapersPipeline
│   │   ├── fetcher.py         #   Multi-source fetch + English translation
│   │   ├── renderer.py        #   HTML rendering
│   │   └── constants.py       #   Source colors
│   ├── trending/              # Trending radar pipeline
│   │   ├── pipeline.py        #   TrendingPipeline
│   │   ├── fetcher.py         #   NewsNow multi-source fetch
│   │   ├── filter.py          #   Keyword / AI filtering + grouping
│   │   └── renderer.py        #   HTML rendering
│   └── wechat/                # WeChat publishing
│       ├── fetcher.py         #   Reuses news/papers fetch + dedup
│       ├── renderer.py        #   WeChat draft HTML rendering
│       ├── cover.py           #   Cover image generation (Pillow)
│       └── api.py             #   WeChat API client
│
├── utils/
│   ├── utils.py               # Shared utilities (dedup / write_files / git_commit / get_now_date_str)
│   └── html_template.py       # HTML templates (CSS / cards / layout)
│
├── config/
│   ├── news_config.yaml       # News config
│   ├── papers_config.yaml     # Papers config
│   ├── trending_config.yaml   # Trending radar config
│   └── wechat_config.yaml     # WeChat publish config
│
├── .github/workflows/
│   ├── daily.yml              # News — daily 07:15
│   ├── papers.yml             # Papers — daily 07:15
│   ├── trending.yml           # Trending — daily 07:00 / 13:00
│   └── wechat.yml             # WeChat — daily 07:15
│
├── test/
│   ├── test.py                # Integration tests for all pipelines (stub + --live mode)
│   └── test_cover.py          # Cover image tests
│
├── requirements.txt           # Python dependencies
└── .env                       # Local environment variables (not tracked)
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/miaohua1982/ai-daily.git
cd ai-daily
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> WeChat cover image generation requires Pillow: `pip install Pillow`

### 3. Configure Environment Variables

Create a `.env` file (or configure via GitHub Secrets):

```bash
# Semantic dedup (Embedding API) — Alibaba Cloud DashScope compatible mode
EMBEDDING_API_KEY=your_embedding_api_key

# AI filtering + paper translation (DeepSeek)
DEEPSEEK_API_KEY=your_deepseek_api_key

# WeChat Official Account publishing (only for generate_wechat.py)
WECHAT_APPID=your_wechat_appid
WECHAT_APPSECRET=your_wechat_appsecret
```

### 4. Run Locally

```bash
# Generate AI News
python generate_daily.py

# Generate AI Papers
python generate_papers.py

# Generate Trending Radar
python generate_trending.py

# Publish WeChat draft (requires WeChat credentials)
python generate_wechat.py
```

### 5. Run Tests

```bash
# Stub mode (fast, no real API calls)
python test/test.py

# Live mode (calls real APIs, may be slow)
python test/test.py --live
```

Test output is written to the `craft/` directory (ignored by `.gitignore`).

---

## Configuration

Each pipeline has its own YAML config file in the `config/` directory.

### Key Config Options

| Config | File | Description |
|---|---|---|
| Data source API URLs | Each `*_config.yaml` | aihot / arXiv / HuggingFace / NewsNow |
| Semantic dedup | Each `*_config.yaml` → `semantic_dedup` | `enabled` / `threshold` / `api_key_env` / `model` |
| AI filtering | `trending_config.yaml` → `filter` + `ai` | `method: keyword\|ai\|both` / `min_score` / `interests` |
| Keyword groups | `trending_config.yaml` → `keywords` | Grouped by domain (AI models / Smart vehicles / Robotics / Finance / International) |
| Paper translation | `papers_config.yaml` → `translation` | `enabled` / `batch_size` / `model` |
| WeChat publishing | `wechat_config.yaml` | Title template / digest template / content limits |

### Semantic Dedup Config Example

```yaml
semantic_dedup:
  enabled: true
  api_key_env: "EMBEDDING_API_KEY"
  base_url: "https://llm-860ckp050tycaw8n.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
  model: "text-embedding-v4"
  threshold: 0.85       # Cosine similarity >= this value is considered duplicate
  batch_size: 10
```

---

## GitHub Actions Deployment

The project runs on GitHub Actions — no self-hosted server needed.

### Required Secrets

Add in **Settings → Secrets and variables → Actions**:

| Secret | Purpose | Required |
|---|---|---|
| `EMBEDDING_API_KEY` | Embedding API for semantic dedup | Required when semantic dedup is enabled |
| `DEEPSEEK_API_KEY` | DeepSeek API for AI filtering + translation | Required when AI filter / translation is enabled |
| `WECHAT_APPID` | WeChat Official Account AppID | Only for WeChat publishing |
| `WECHAT_APPSECRET` | WeChat Official Account AppSecret | Only for WeChat publishing |
| `SERVERCHAN_SENDKEY` | ServerChan notification key | Optional, receive success / failure notifications |

### Actions Schedule

| Workflow | Beijing Time | UTC | Frequency |
|---|---|---|---|
| `daily.yml` | 07:15 | 23:15 (previous day) | Daily |
| `papers.yml` | 07:15 | 23:15 (previous day) | Daily |
| `trending.yml` | 07:00 / 13:00 | 23:00 / 05:00 | Twice daily |
| `wechat.yml` | 07:15 | 23:15 (previous day) | Daily |

All Actions support `workflow_dispatch` for manual triggering.

---

## Pipeline Details

### AI News (NewsPipeline)

```
aihot API ──→ fetch_data ──→ dedup_data ──→ generate_html ──→ write_files ──→ git_commit
newsnow API ─┘    (URL + semantic dedup)    (category render)  (index + archive)
```

- Primary source: AI HOT; auto-fallback to NewsNow when unavailable
- Each news item carries its own `publishTime` for independent time rendering
- Grouped by category (AI / Products / Research, etc.)

### AI Papers (PapersPipeline)

```
aihot ──→ fetch_data ──→ translate ──→ dedup_data ──→ generate_html ──→ write_files ──→ git_commit
arXiv ──┤    (merge)      (EN→ZH)      (URL + semantic)  (card render)
HF ─────┘
```

- Three-source merge: AI HOT papers + arXiv category search + HuggingFace Daily Papers
- English titles / abstracts auto-translated to Chinese (DeepSeek, batch translation)
- Cross-source dedup (same paper may appear on both arXiv and HuggingFace)

### Trending Radar (TrendingPipeline)

```
NewsNow ──→ fetch_data ──→ dedup_data ──→ filter_data ──→ generate_html ──→ write_files ──→ git_commit
(8 sources)   (URL + semantic) (keyword/AI)   (grouped render)   (index + archive)
```

- 8 data sources in 3 groups: General trending / Finance / International
- AI filtering: DeepSeek scores each news item (0-1), keeps items >= `min_score`
- Grouped into 5 domains: International affairs / Finance / AI models / Smart vehicles / Robotics
- Updated twice daily (07:00 / 13:00), archive filenames include hour suffix `YYYY-MM-DD-HH`

### WeChat Draft (generate_wechat.py)

```
gd.fetch_data ──→ gd.dedup_data ─┐
gp.fetch_data ──→ gp.dedup_data ─┤→ render_wechat_html → generate_cover → upload_image → create_draft
                                 │                       (Pillow draw)     (WeChat API)     (draft box)
```

- Reuses news + papers fetch + dedup steps, truncates to top N items
- Pillow auto-generates cover image (date + item count)
- Creates draft via WeChat Official Account API — does not auto-publish
- Success / failure notifications via ServerChan

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Dependencies | PyYAML (only hard dependency), Pillow (WeChat cover image, optional) |
| CI/CD | GitHub Actions |
| AI Services | DeepSeek (filtering + translation), Alibaba Cloud DashScope (Embedding semantic dedup) |
| Data Sources | AI HOT API, arXiv API, HuggingFace API, NewsNow API |
| WeChat | WeChat Official Account Platform API |
| Notifications | ServerChan |

---

## Extending

### Adding a New Pipeline

1. Create `src/<name>/` directory with `pipeline.py`, `fetcher.py`, `renderer.py`
2. Inherit from `GeneratorPipeline`, implement `fetch_data` and `generate_html`
3. Override `filter_data` if a filtering step is needed
4. Create `generate_<name>.py` entry script
5. Create `config/<name>_config.yaml` config file
6. Add `.github/workflows/<name>.yml` scheduled workflow

```python
from src.pipeline import GeneratorPipeline

class MyPipeline(GeneratorPipeline):
    OUTPUT_DIR  = Path(__file__).parent.parent.parent
    ARCHIVE_DIR = OUTPUT_DIR / "my-archive"
    INDEX_FILE  = OUTPUT_DIR / "my.html"
    CONFIG_FILE = OUTPUT_DIR / "config" / "my_config.yaml"

    def fetch_data(self, config):
        return _fetch_impl(config)

    def generate_html(self, items):
        return _render_impl(items)
```

Only two abstract methods need implementing — `dedup_data`, `write_files`, `git_commit`, and `run` are all inherited from the base class.

---

## License

MIT
