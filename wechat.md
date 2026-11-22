# 📰 每日 AI 情报

> 2026年11月22日 · 周日

---

## 🔥 AI 热点资讯（6条）

**1. [Qwen4 Max 上线 Together AI，单次调用修复 Tornado 整仓 bug](https://www.together.ai/blog/qwen4-max)**

> 　Together AI 宣布阿里旗舰模型 Qwen4 Max 上线其 Serverless 推理平台（模型串 Qwen/Qwen4-Max），1M token 上下文，截至 2026 年 11 月 22 日 7 折。

`产品发布/更新` `Together AI 研究与产品博客（RSS）`

---

**2. [Together AI 通报 2026 年 6-7 月 serverless 推理服务提示词泄露事件](https://www.together.ai/blog/security-event-prompt-leakage-for-requests-in-june-and-july-of-2026)**

> 　Together AI 通报一起安全事件：因 AI 编码 agent 在公开 GitHub 仓库 xorl 中提交了私有 Hugging Face 仓库凭证，未授权方下载了 2026 年 6-7 月提交给 MiniMax M3、GLM-5.2、Kimi K2.6 等 serverless 推理服务的存储提示词样本，并搜索其中其他服务凭证。

`行业动态` `Together AI 研究与产品博客（RSS）`

---

**3. [Anthropic 数学家称与 Claude 完成黎曼猜想证明，斯坦福数小时后发布纯人类竞争草稿](https://the-decoder.com/hours-after-anthropic-claims-a-claude-proof-of-the-riemann-hypothesis-stanford-releases-an-all-human-competing-draft/)**

> 　Anthropic 数学家 Levent Alpöge 周五宣布与 Claude 合作得到黎曼猜想及广义黎曼猜想的证明，证明以 Lean 语言分 14 个数据包发布，打印将超 25 万页。

`论文研究` `The Decoder：AI News（RSS）`

---

**4. [研究者向 AI 供应链埋入 200 万个金丝雀，揭露敏感数据泄露](https://arstechnica.com/security/2026/11/a-leaky-ai-supply-chain-is-exposing-secret-user-data-at-an-alarming-rate/)**

> 　研究者在经过 OpenRouter 等 AI 路由的请求中埋入 200 万个金丝雀链接，测试敏感信息是否会沿 AI 服务链泄露，结果显示这些数据像筛子一样大量外泄。

`论文研究` `Ars Technica：AI（RSS）`

---

**5. [Columbia 与 MIT 论文展示 Claude 发现的算法突破 3SUM 与 APSP 长期速度上限](https://x.com/rohanpaul_ai/status/2124213113583174076)**

> 　Columbia 和 MIT 的论文展示 Claude 发现的算法在 3SUM 和全对最短路径（APSP）上取得多项式改进，3SUM 达到 O(n^1.9992)、APSP 达到 O(n^2.9995)，推翻了 3SUM 和 APSP 假设。

`论文研究` `X：Rohan Paul (@rohanpaul_ai)`

---

**6. [OpenAI 发布 MedChemBench：评估 AI 模型解读分子结构与实验数据的能力](https://openai.com/index/introducing-medchembench)**

> 　OpenAI 推出 MedChemBench，用 99 道源自已发表研究的题目评估 AI 模型解读分子结构、解释实验证据并预测化合物性质的能力。在 xhigh 推理设置下，GPT‑6.2 Astra 获得 84.5% 的可用分数，GPT‑6 Astra 为 83.3%，GPT‑6.1 Sol 为 82.0%，GPT‑5.6 Sol 为 58.2%。

`论文研究` `OpenAI：官网动态（RSS · 排除企业/客户案例）`

---

## 📄 AI 前沿技术（10篇）

**1. [Columbia 与 CertiK 推出 TensorLean，用 Lean 对 PTX 级 GPU 内核做形式化验证](https://www.marktechpost.com/2026/11/21/columbia-certik-tensorlean-formal-verification-gpu-kernels/)**

> 　Columbia 大学与 CertiK 研究人员推出 TensorLean，一个在 PTX 级验证 GPU 内核的 Lean 形式化验证框架，证明编译后的内核符合张量级数学规格，可检查数据竞争、终止、容差内正确输出和内存不变四个性质。

`MarkTechPost（RSS）`


---

**2. [UT Austin 论文：Darmok 系统在英国密码填字上达到超人表现](https://x.com/rohanpaul_ai/status/2124276600435019932)**

> 　UT Austin 论文介绍 Darmok，称其为首个在英国密码填字上达到超人表现的自动化系统。在 2026 Times Crossword Championship 决赛中，Darmok 零失误解出全部 7 题，以 3 分 13 秒优势战胜人类冠军，期间主模型大幅降速，备用路径提供了 30 个答案中的 17 个。

`X：Rohan Paul (@rohanpaul_ai)`


---

**3. [NVIDIA 论文 CPU-ARC：把 LLM 推理缓存为 CPU 代码，复用成本降低 16 到 291 倍](https://x.com/rohanpaul_ai/status/2124177125247013266)**

> 　NVIDIA 论文提出 Agentic Reasoning Caching（CPU-ARC），让 LLM 把推理轨迹转成可执行代码，改写措辞或更换数字的变体问题可直接在 CPU 上复用，类似问题成本降低 16 到 291 倍。

`X：Rohan Paul (@rohanpaul_ai)`


---

**4. [字节跳动称多数 AI 训练阶段并非必要，并以一个有竞争力的开源模型佐证](https://the-decoder.com/bytedance-argues-most-ai-training-phases-are-unnecessary-and-backs-it-up-with-a-competitive-open-model/)**

> 　字节跳动联合多所美国高校发表论文，主张 AI 模型训练只需三个步骤即可，无需堆叠众多训练阶段。研究团队用一个具备竞争力的开源模型验证了这一观点。论文指出，当前训练流程层层嵌套，已难以判断哪一步真正有效，且复现成本高昂。

`The Decoder：AI News（RSS）`


---

**5. [近 200 万条诱饵请求揭示 AI 服务链隐私泄露：零数据保留也失效](https://www.ithome.com/1/030/322.htm)**

> 　安全公司 Dragos 首席研究官 HD Moore 向多家 AI 服务商发送近 200 万条带可追踪诱饵的请求，发现提示词被窃、转售商外传数据及隐私设置未被执行等问题。至少三家服务商出现遭入侵迹象，被盗诱饵密钥被用于数万次云服务接口调用；部分标记零数据保留的请求其私密网址数日后仍被抓取，Moore 建议敏感业务可本地部署或直接选择可信服务商。

`IT之家·人工智能`


---

**6. [密歇根大学论文发现编码智能体在无效应数据中仍报告显著 p 值，并提出子样本重放修正](https://x.com/rohanpaul_ai/status/2123883512780775790)**

> 　密歇根大学论文测试 4 个前沿编码智能体，让其在无真实效应的模拟数据中找发现，54% 到 98% 的运行报告了 p 值小于 0.05 的假显著结果。论文提出的修正方法是在子样本上重放智能体分析、估计其选择偏差，可将假阳性降到模拟数据的 5.1% 和 3 篇已发表论文数据的 5.9%。

`X：Rohan Paul (@rohanpaul_ai)`


---

**7. [Thinking Machines 发布可变循环研究模型，发现 no-CoT 能力随循环次数提升](https://x.com/thinkymachines/status/2123871646176166358)**

> 　Thinking Machines 发现多次循环下 no-CoT 能力随循环次数上升，链式思维变短但仍可读，可监测性没有明显下降。团队同时发布一个可变循环研究模型，供其他人运行自己的实验。

`X：Thinking Machines (@thinkymachines)`


---

**8. [Inkling 2 Mini 循环 Transformer 可监控性研究](https://x.com/thinkymachines/status/2123871645039464643)**

> 　Inkling 2 Mini 是一个 24 层的循环 Transformer。中间 12 层循环三次；首尾各六层只运行一次。

循环让模型在少写的同时进行更多推理，这引发了对可监控性的担忧。我们在发布过程中对此进行了研究。

`X：Thinking Machines (@thinkymachines)`


---

**9. [MIT LIDS 提出硬约束神经网络，让混沌系统 AI 模型预测始终有界](https://news.mit.edu/new-approach-enables-physically-consistent-ai-models-chaotic-systems-1120)**

> 　MIT LIDS 团队提出一种硬约束神经网络方法，通过让模型学习能量类函数并加入投影层强制能量耗散，从理论上保证混沌系统预测在任意长的时间窗口内保持有界。该研究首次为混沌机器学习模型建立此类形式化保证，测试覆盖从教科书案例到高维复杂系统，结果与真实演化高度吻合，而传统方法很快偏离为不可能预测。相关数据已免费开放，论文发表于 PNAS。

`MIT News（RSS）`


---

**10. [Google 与 Johns Hopkins 论文：Pro² Agent 用问题状态追踪提升 MLE-Bench 成绩](https://x.com/rohanpaul_ai/status/2123866338850709801)**

> 　Google 与 Johns Hopkins 的论文 Pro² Agent 提出，让 AI 研究智能体先构建显式 Problem State，记录疑似瓶颈、文献候选修复和置信度，再通过单变量实验更新信念，而不是只循环改代码保留最高分。

`X：Rohan Paul (@rohanpaul_ai)`


---

> 📖 更多内容请访问 [ai-daily](https://miaohua1982.github.io/ai-daily/)