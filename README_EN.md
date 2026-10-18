# AI Daily

<!-- 【文档同步标识｜2026-10-18】同步新接口迁移、来源异常隔离、译文 ID 对齐、自然周过滤和离线白盒测试；未修改运行代码或定时配置。 -->

> Automatically aggregate AI news, academic papers, and trending topics daily into static HTML pages and WeChat Official Account drafts.

English | [中文](./README.md)

---

## Overview

AI Daily is a fully automated content aggregation pipeline that fetches from multiple data sources on a daily schedule, deduplicates, filters, and translates the content, then generates three independent static HTML pages with an optional WeChat draft publish step. All workflows are triggered by GitHub Actions — no server required.

### Three Pipelines + One Publishing Channel

| Module | Entry Script | Data Sources | Output | Schedule (Beijing Time) |
|---|---|---|---|---|
| **AI News** | `generate_daily.py` | AI HOT + NewsNow (fallback) | `daily_news.html` | 07:15 |
| **AI Papers** | `generate_papers.py` | AI HOT first; arXiv + HuggingFace fallback | `papers.html` | 07:15 |
| **Trending Radar** | `generate_trending.py` | NewsNow multi-source (Weibo, Toutiao, Jin10, CLS, Wallstreetcn, Cankaoxiaoxi, Zaobao, Thepaper) | `trending.html` | 07:00 / 13:00 |
| **WeChat Draft** | `generate_wechat.py` | Reuses fetching; deduplicates news and papers together | WeChat Official Account draft | 07:15 |
| **Weekly Papers** | `generate_wechat_papers_weekly.py` | HuggingFace + arXiv; Beijing natural week | HTML / Markdown and optional WeChat draft | Sunday 17:00 |

### Live Preview

👉 **[https://miaohua1982.github.io/ai-daily/](https://miaohua1982.github.io/ai-daily/)**

---

## Key Features

- **Multi-source aggregation**: AI HOT API, arXiv, HuggingFace Daily Papers, NewsNow trending feeds
- **Smart deduplication**: URL dedup + embedding-based semantic dedup (cosine similarity, configurable threshold)
- **AI filtering**: LLM scoring on news headlines (DeepSeek), grouped by interest domains
- **Auto translation**: arXiv / HuggingFace English papers translated to Chinese (DeepSeek), matched by batch-local ID; missing translations preserve originals
- **Independent fallback sources**: an arXiv failure does not prevent HuggingFace fetching, or discard its successful results
- **Natural-week selection**: weekly papers are filtered from Monday midnight through the target day in Beijing time
- **WeChat publishing**: Auto-generated cover image + draft creation, with ServerChan notifications
- **Historical archive**: Daily archive files generated automatically; index page lists history
- **Pipeline abstraction**: Three pipelines unified under `GeneratorPipeline` — consistent interface, easily extensible

---

## Architecture

```
GeneratorPipeline (abstract base class, src/pipeline.py)
  ├── fetch_data()      # abstract — implemented by subclass
  ├── dedup_data()      # default — calls utils.dedup_data (URL + semantic)
  ├── filter_data()     # default passthrough — news/papers filter summaries; trending filters interests
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
├── generate_wechat_papers_weekly.py # Weekly papers entry point
├── generate_wechat_video.py   # Upload existing video as permanent material
├── index.html                 # Landing page (navigation + archive list)
├── archive/                    # Runtime output: history archives (news / papers / trending / wechat_draft)
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
│       ├── fetcher.py         #   Fetch/filter and cross-section dedup
│       ├── weekly_fetcher.py  #   Beijing natural-week selection
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
│   ├── wechat_config.yaml     # WeChat daily config
│   └── weekly_config.yaml     # Independent weekly config
│
├── .github/workflows/
│   ├── daily.yml              # News — daily 07:15
│   ├── papers.yml             # Papers — daily 07:15
│   ├── trending.yml           # Trending — daily 07:00 / 13:00
│   ├── wechat.yml             # WeChat — daily 07:15
│   └── wechat_papers_weekly.yml # Weekly — Sunday 17:00
│
├── test/
│   ├── test.py                # Unified offline pytest entry point
│   ├── conftest.py            # Network/process/credential isolation
│   ├── test_cover.py          # PNG and font fallback tests
│   ├── test_translation_alignment.py # Translation ID regression
│   ├── test_weekly_window.py  # Week and timezone boundaries
│   ├── test_known_defects.py  # Known defects and fixed regressions
│   └── README.md              # Full testing instructions
│
├── requirements.txt           # Runtime dependencies
├── requirements-test.txt      # Separate testing dependencies
├── pytest.ini                 # Test discovery rules
├── .coveragerc                # Python line/branch coverage
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

# Local preview only (wechat.md / wechat.html, no WeChat API, no credentials needed)
WECHAT_LOCAL_ONLY=1 python generate_wechat.py
# or with CLI flag: python generate_wechat.py --local-only

# Generate and publish weekly draft (requires WeChat credentials)
python generate_wechat_papers_weekly.py
# Local preview only (wechat_papers_weekly.md / .html, no WeChat API, no credentials needed)
WECHAT_LOCAL_ONLY=1 python generate_wechat_papers_weekly.py
# or with CLI flag: python generate_wechat_papers_weekly.py --local-only
```

### 5. Run Tests

<!-- 【测试说明更新｜2026-10-18】Document isolated pytest tests and actual coverage limits. -->
```bash
python -m pip install -r requirements-test.txt
python -B -m pytest -q
# Compatible entry point; runs the same offline suite
python -B test/test.py

mkdir -p craft/coverage
python -B -m coverage run -m pytest -q
python -B -m coverage report
python -B -m coverage html -d craft/coverage/html
python -B -m coverage json -o craft/coverage/coverage.json
```

For the existing local environment, replace `python` with `../venv/bin/python`. Tests block unstubbed HTTP, sockets and subprocesses, isolate real API credentials, and write generated files only to pytest temporary directories. Coverage reports go to the ignored `craft/coverage/` directory. The old `--live` test mode has been removed.

Snapshot on 2026-10-18: **310 tests; 307 passed, 3 strict xfailed; Python line coverage 99.77%, branch coverage 99.37%**. Expected failures identify unresolved defects and are not passes. Re-run to obtain current figures. Python coverage does not measure JavaScript inside HTML, GitHub Actions execution, or every possible input/loop path.

Three remaining defect regressions concern empty list entries in the no-PyYAML fallback parser, a missing `archive/` prefix in pipeline Git paths, and unescaped `</script>` in embedded paper JSON. Translation alignment and natural-week filtering have been fixed and their regressions must pass. See [test/README.md](test/README.md) for details. To expose remaining defects as ordinary failures, run `python -B -m pytest test/test_known_defects.py --runxfail -q` (nonzero exit expected).

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

### AIHOT v1 Migration

<!-- 【接口迁移说明｜2026-10-18】Keep endpoint and field mapping documentation aligned with fetching code. -->
All AIHOT base URLs, including the disabled weekly configuration, now use `https://aihot.news/api/v1`. The legacy `/api/public/*` shutdown date is 2026-10-31; see the [official migration guide](https://aihot.news/agent?tab=api#legacy-api-migration).

| Call | v1 adaptation |
|---|---|
| Dated / latest daily | `/dailies/{date}` / `/dailies/latest`; read `report.sections` |
| Paper list | `/items?mode=all&category=paper&window=7d&by=published&limit=...` |
| Count and dates | Keep local config `take`, send API `limit`; narrow the 7-day window locally using `days_back` |
| Pagination | Read `page.hasMore` / `page.nextCursor`; encode the cursor and start each run from page one |
| Original URL / source | Adapt `links.original` / `source.name` to existing internal fields for rendering and deduplication |

Daily `flashes` are not added to the existing summary-based article flow. The list API is a rolling 7-day source, not historical backfill. Existing workflow schedules are unchanged.

### Semantic Dedup Config Example

```yaml
semantic_dedup:
  enabled: true
  api_key_env: "EMBEDDING_API_KEY"
  base_url: "https://llm-860ckp050tycaw8n.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
  model: "text-embedding-v4"
  threshold: 0.75       # Cosine similarity >= this value is considered duplicate
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
| `wechat_papers_weekly.yml` | Sunday 17:00 | Sunday 09:00 | Weekly |

All Actions support `workflow_dispatch` for manual triggering.

---

## Pipeline Details

### AI News (NewsPipeline)

```
AIHOT dated daily -> latest daily -> NewsNow (existing fallback order)
  -> field adaptation -> URL/semantic dedup -> summary filter -> HTML -> files/archive -> Git
```

- Read daily articles from `report.sections`; adapt links, sources and categories to existing fields.
- Preserve `publishTime`; minimum summary length is configured by `filter.min_summary_len`.

### AI Papers (PapersPipeline)

```
AIHOT has papers -> use them directly
AIHOT has no papers -> arXiv + HuggingFace (independent exception handlers) -> merge -> translate
  -> URL/semantic dedup -> summary filter -> HTML -> files/archive -> Git
```

- This is primary-first fetching, not a three-source merge on every run. One backup failing does not prevent the other from running or discard its successful result.
- Translation results match papers by integer ID within each batch, never by `zip` position. Missing translations preserve originals; missing, invalid or out-of-range IDs are ignored. Duplicate IDs keep the first result with a warning.
- Title/summary types are validated separately; invalid fields preserve originals, empty output does not count as success, and IDs restart for each batch.
- Existing internal fields remain compatible with deduplication, web pages and WeChat rendering.

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
Fetch/filter news and papers -> unified URL/semantic dedup (news wins) -> per-section limits
  -> local HTML/Markdown and archives
  -> unless local-only: cover -> upload -> create draft
```

- Defaults: at most 10 news items and 10 papers. Local-only mode still fetches/deduplicates but does not upload or create a draft.
- Pillow generates the cover. The WeChat API creates a draft, not a public post. Workflow steps send success/failure notifications through ServerChan.

### Weekly Papers (generate_wechat_papers_weekly.py)

<!-- 【自然周修复说明｜2026-10-18】Separate fetch-day count from date offsets; retain ordinary rolling-window behavior. -->
- Fetch HuggingFace and arXiv directly, skipping AIHOT, with independent exception handling.
- HF queries Monday through the target day. After merging, filter `publishedAt` to **Monday 00:00 inclusive through midnight after the target day exclusive**, in Beijing time.
- Convert UTC/Z and offset timestamps to Beijing time; treat naive timestamps as UTC and discard missing/unparseable timestamps.
- On Sunday 2026-10-18, retain Beijing dates October 12–18. The previous Sunday is excluded; UTC October 11 at 16:00 equals Monday midnight in Beijing and is retained.
- Then filter summaries, deduplicate, rank (HF votes first), take `top_n` (default 30), and translate selected papers. Generate HTML/Markdown and an optional WeChat draft. The ordinary papers pipeline's shared rolling-date filter is unchanged.

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
    ARCHIVE_DIR = OUTPUT_DIR / "archive" / "my"
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
