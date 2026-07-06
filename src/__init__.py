"""
src — 业务逻辑分层模块。

每个 generate_*.py 的辅助函数按职责拆分到独立子目录：

  - src/papers/    论文管线（fetcher / renderer）— dedup 已提取至 utils.dedup_data
                   入口：from src.papers import fetch_data, generate_html
                   编排：generate_papers.py

  - src/news/      新闻管线（fetcher / renderer + constants）— dedup 已提取至 utils.dedup_data
                   入口：from src.news import fetch_data, generate_html
                   编排：generate_daily.py

  - src/trending/  趋势雷达管线（fetcher / dedup / filter / renderer）
                   入口：from src.trending import fetch_data, dedup_data, filter_data, generate_html
                   编排：generate_trending.py

注意：papers 和 news 的同名函数请务必通过子包路径导入，避免歧义。
      例如 from src.papers.fetcher import fetch_data（非 from src import fetch_data）。
"""
