# ai-daily 白盒测试

## 运行

使用项目已有虚拟环境；测试依赖单独列在根目录 requirements-test.txt：

```sh
../venv/bin/python -m pip install -r requirements-test.txt
../venv/bin/python -B -m pytest -q
# 兼容原入口：
../venv/bin/python -B test/test.py
```

测试默认离线：禁止真实 HTTP、socket 和子进程，清除测试中的 API 凭证，
不读取真实 .env（测试 dotenv 自身时也只使用临时假数据）。文件写入 pytest
临时目录。不得取消这些保护后运行发布测试。Git、微信上传、建草稿和视频
上传均模拟；捕获异常后偷偷使用假数据的旧 live 模式已经移除。

## 覆盖率

```sh
mkdir -p craft/coverage
../venv/bin/python -B -m coverage run -m pytest -q
../venv/bin/python -B -m coverage report
../venv/bin/python -B -m coverage html -d craft/coverage/html
../venv/bin/python -B -m coverage json -o craft/coverage/coverage.json
```

.coveragerc 启用分支统计，包含 src、utils 和全部六个 generate 入口。
没有为达到百分比增加 `pragma: no cover`、`pragma: no branch` 或排除业务模块。
coverage 默认不计算抽象方法体等代码，JSON 会列出工具默认 excluded_lines。
Python 模板字符串中的 JavaScript 不属于 Python 分支统计；没有把它宣称为
浏览器 JavaScript 的 100% 覆盖。GitHub Actions YAML 也不属于 Python 覆盖率。

100% 行/分支覆盖也不等于所有执行路径：循环次数和输入组合会产生无穷多路径。
当前保留生产代码中的不可达/非法输入分支，不通过修改生产逻辑来刷覆盖率。

## 文件分工

- conftest.py：副作用隔离与公共样本。
- test_utils.py：配置、YAML fallback、Embedding、语义去重、HTTP、日期和 Git。
- test_fetchers.py：AIHOT v1、arXiv XML、HF JSON、翻译、重试及来源异常隔离。
- test_translation_alignment.py：译文 ID 精确匹配、缺项、乱序、重复/非法 ID、异常字段和批次隔离回归。
- test_filters_renderers.py：关键词/AI 筛选与网页/微信 HTML、Markdown。
- test_cover.py：日报/周报 PNG 和跨平台字体回退。
- test_publication.py：微信 HTTP、token、上传、草稿、视频与命令行流程。
- test_pipelines_weekly.py：管线、入口代理、跨区去重及周报精选。
- test_boundaries.py：脚本入口和可达边界补充。
- test_known_defects.py：尚未修复的业务缺陷，使用带原因的 strict xfail 明示。

## 已知缺陷不是“测试通过”

`3 xfailed` 意味着三个契约断言仍不成立，不代表生产行为正确。strict=True
使意外修复后的 XPASS 也报错，要求维护者移除对应标记、确认修复。
可独立运行以下命令将缺陷全部显示为普通失败（预期非零退出）：

```sh
../venv/bin/python -B -m pytest test/test_known_defects.py --runxfail -q
```

目前未修复：简易 YAML 的空列表项、Git 归档路径少 archive/ 前缀、
论文 JSON 未转义 `</script>`。

<!-- 【修复记录｜2026-10-18】翻译按批次内 ID 匹配，缺项回归已移除 xfail。 -->
翻译缺 ID 时错位已修复；缺项、乱序、重复/非法 ID、异常字段和跨批编号
均由普通回归用例验证。
这些问题仅添加证据和回归测试，没有顺带修改生产逻辑。

<!-- 【修复记录｜2026-10-18】周报独立按北京时间过滤自然周，不修改共享滚动窗口。 -->
周报日期边界已修复；test_weekly_window.py 覆盖周一、周中、周日及 UTC/北京时间跨日边界。
