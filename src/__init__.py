"""
src — 业务逻辑分层模块。

每个 generate_*.py 的辅助函数按职责拆分到独立子目录：

  - src/pipeline.py  管线抽象接口（ABC），定义 fetch→dedup→filter→render→write→git 六步
                     GeneratorPipeline.run() 为模板方法，子类只需实现 fetch_data + generate_html

  - src/papers/    论文管线（pipeline / fetcher / renderer / constants）
                   PapersPipeline 继承 GeneratorPipeline，入口：generate_papers.py

  - src/news/      新闻管线（pipeline / fetcher / renderer / constants）
                   NewsPipeline 继承 GeneratorPipeline，入口：generate_daily.py

  - src/trending/  趋势雷达管线（pipeline / fetcher / filter / renderer）
                   TrendingPipeline 继承 GeneratorPipeline，覆盖 filter_data + date_str（-HH 后缀），入口：generate_trending.py

注意：papers 和 news 的同名函数请务必通过子包路径导入，避免歧义。
      例如 from src.papers.fetcher import fetch_data（非 from src import fetch_data）。
"""
