# 📰 每日 AI 情报

> 2026年11月21日 · 周六

---

## 🔥 AI 热点资讯（10条）

**1. [Thinking Machines Lab 发布可跑在笔记本上的开源权重模型 Inkling 2 Mini](https://thinkingmachines.ai/news/inkling-2-mini/)**

> 　Thinking Machines Lab 发布开源权重模型 Inkling 2 Mini，采用循环 Transformer 架构，将中间 12 层每 token 运行三次，总参数 26.4B、激活 3.4B，内存占用约 20GB，可在 32GB 内存以上的 Mac 本地运行。

`模型发布/更新` `Thinking Machines Lab：News（网页）`

---

**2. [腾讯混元开放 Hy4 权重](https://x.com/TencentHunyuan/status/2123625549147070538)**

> 　腾讯混元发布 Hy4 开放权重，定位原生多模态旗舰 MoE 模型，总参数 770B、激活 49B，支持 1M 上下文。同步发布含安全评估报告的 Hy4 System Card，并提供 GitHub、Hugging Face 权重与 GGUF 下载链接，团队将于本周五 8–10 AM PT 在 r/LocalLLaMA 举行 AMA。

`模型发布/更新` `X：腾讯混元 (@TencentHunyuan)`

---

**3. [Google 发布 Gemini 4 Hydrogen，已上线 Gemini 应用和 Search](https://x.com/Google/status/2123825847815561261)**

> 　Google 宣布 Gemini 4 Hydrogen 正式上线，主打速度和日常任务，现已可在 Gemini 应用和 Search 中使用。该模型面向多样化的智能体工作流设计，强调快速高效执行；官方称其能更紧密地遵循指令、更准确地调用工具，用更少的来回沟通产出可靠结果。

`模型发布/更新` `X：Google (@Google)`

---

**4. [ChatGPT 推出 Space：统一管理页面、幻灯片、图片与文件](https://x.com/ChatGPT/status/2123850915061104735)**

> 　ChatGPT 官方宣布侧边栏中的 Space 成为 pages、slides、images、files 和 uploads 的新家。用 ChatGPT 可写页面、做研究、生成图片并创建交互式图表，把想法变成带图片和图形的幻灯片并邀请他人协作；页面和幻灯片还可从已连接的工具自动更新。

`产品发布/更新` `X：ChatGPT (@ChatGPT)`

---

**5. [browser-use 1.0 发布：用一个 Python REPL 工具替代 24 个浏览器动作](https://browser-use.com/posts/browser-use-1-0)**

> 　Browser Use 发布 browser-use 1.0，用单一 python 持久 REPL 加原生 Chrome DevTools Protocol 访问替代 0.x 的 24 个浏览器动作。

`产品发布/更新` `Browser Use`

---

**6. [Google 回顾 Duplex 十年演进：如何在 Gemini Tasks 中替用户打电话给商家](https://research.google/blog/how-google-duplex-evolved-to-also-call-businesses-for-you-in-gemini/)**

> 　Google Research 回顾 Duplex 十年架构演进，并介绍本周在 Gemini App Tasks 中上线的自动致电商家功能。

`产品发布/更新` `Google Research：Blog（网页）`

---

**7. [Anthropic 数学家 Levent Alpöge 宣布与 Claude 合作证明黎曼猜想，放出 1737 万行 Lean 代码](https://mp.weixin.qq.com/s/8Zi3nfwddzFy6cZsK2_KxA)**

> 　Anthropic 数学家 Levent Alpöge 在个人网站宣布与 Claude 合作证明了黎曼猜想，没有论文，只放出 14 个压缩包共 175187 个 Lean 文件、1737 万行代码。

`论文研究` `公众号：数字生命卡兹克`

---

**8. [METR 发布 2026 年 11 月能力测量更新：AI R&D 相关能力每约 3.6 个月翻倍且更难测量](https://metr.org/blog/2026-11-20-q4-2026-capability-update/)**

> 　METR 发布截至 Opus 5.5 和 GPT-6 Astra 的能力评测更新，发现在 TH1.1 与 TH2 任务上模型时间视野约每 3.6 个月翻倍，可验证子集翻倍时间约 1.65 个月。

`论文研究` `METR：Research（网页）`

---

**9. [MiniMax 内部模型 MIM 实现多项密码分析实用攻击并开源验证轨迹](https://www.minimax.io/blog/practical-cryptanalysis-with-minimaxs-latest-internal-model)**

> 　MiniMax 研究团队用内部研究模型 MIM 对现代密码方案做自动化密码分析，报告称在 NIST 候选算法、同行评审方案和公开挑战基准上取得多个此前无实用攻击方案的首个实用破解，并把部分理论攻击变为可执行攻击。

`论文研究` `MiniMax：Blog（网页）`

---

**10. [Runway 详解如何构建智能体驱动的软件工厂](https://runwayml.com/news/engineering/building-a-software-factory)**

> 　Runway 介绍了逐步把软件交付各环节交给智能体完成的实践。智能体 10 月驱动了 38% 的合并 PR（6 月仅 0.1%），首次批准等待中位数从超过 2 小时降至约 5 分钟；AI 单独批准的 PR 回滚率约千分之一，低于人工批准的约 1/200。

`技巧与观点` `Runway：News（网页）`

---

## 📄 AI 前沿技术（10篇）

**1. [近 200 万条诱饵请求揭示 AI 服务链隐私泄露：零数据保留也失效](https://www.ithome.com/1/030/322.htm)**

> 　安全公司 Dragos 首席研究官 HD Moore 向多家 AI 服务商发送近 200 万条带可追踪诱饵的请求，发现提示词被窃、转售商外传数据及隐私设置未被执行等问题。至少三家服务商出现遭入侵迹象，被盗诱饵密钥被用于数万次云服务接口调用；部分标记零数据保留的请求其私密网址数日后仍被抓取，Moore 建议敏感业务可本地部署或直接选择可信服务商。

`IT之家·人工智能`


---

**2. [OpenAI 推出 MedChemBench 基准，评估 AI 辅助药物研发能力](https://www.ithome.com/1/030/301.htm)**

> 　OpenAI 发布 MedChemBench 基准，用 99 道取自 117 篇论文与专利、涉及 761 个分子结构的题目评估 AI 的药物化学推理能力。在 xhigh 推理档下，GPT-6.2 Astra 获 84.5% 可用分数，GPT-6 Astra 为 83.3%，GPT-6.1 Sol 为 82.0%，GPT-5.6 Sol 仅 58.2%。

`IT之家·人工智能`


---

**3. [安全研究员在 AI 服务链中植入 200 万个金丝雀密钥测试数据泄露](https://arstechnica.com/security/2026/11/a-leaky-ai-supply-chain-is-exposing-secret-user-data-at-an-alarming-rate/)**

> 　安全研究员 HD Moore 在经由 AI 路由（如 OpenRouter、Vercel）转发的提示词中植入 200 万个从未使用过的金丝雀秘密，包括 AWS 访问密钥、SSH 密码和私有 git 仓库引用，用于追踪敏感信息在 AI 服务链中的泄露路径。实验发现这些信息会像筛子一样外泄，金丝雀机制能定位链条中每个负责泄露的环节。

`Ars Technica：AI（RSS）`


---

**4. [密歇根大学论文发现编码智能体在无效应数据中仍报告显著 p 值，并提出子样本重放修正](https://x.com/rohanpaul_ai/status/2123883512780775790)**

> 　密歇根大学论文测试 4 个前沿编码智能体，让其在无真实效应的模拟数据中找发现，54% 到 98% 的运行报告了 p 值小于 0.05 的假显著结果。论文提出的修正方法是在子样本上重放智能体分析、估计其选择偏差，可将假阳性降到模拟数据的 5.1% 和 3 篇已发表论文数据的 5.9%。

`X：Rohan Paul (@rohanpaul_ai)`


---

**5. [Thinking Machines 发布可变循环研究模型，发现 no-CoT 能力随循环次数提升](https://x.com/thinkymachines/status/2123871646176166358)**

> 　Thinking Machines 发现多次循环下 no-CoT 能力随循环次数上升，链式思维变短但仍可读，可监测性没有明显下降。团队同时发布一个可变循环研究模型，供其他人运行自己的实验。

`X：Thinking Machines (@thinkymachines)`


---

**6. [Inkling 2 Mini 循环 Transformer 可监控性研究](https://x.com/thinkymachines/status/2123871645039464643)**

> 　Inkling 2 Mini 是一个 24 层的循环 Transformer。中间 12 层循环三次；首尾各六层只运行一次。

循环让模型在少写的同时进行更多推理，这引发了对可监控性的担忧。我们在发布过程中对此进行了研究。

`X：Thinking Machines (@thinkymachines)`


---

**7. [MIT LIDS 提出硬约束神经网络，让混沌系统 AI 模型预测始终有界](https://news.mit.edu/new-approach-enables-physically-consistent-ai-models-chaotic-systems-1120)**

> 　MIT LIDS 团队提出一种硬约束神经网络方法，通过让模型学习能量类函数并加入投影层强制能量耗散，从理论上保证混沌系统预测在任意长的时间窗口内保持有界。该研究首次为混沌机器学习模型建立此类形式化保证，测试覆盖从教科书案例到高维复杂系统，结果与真实演化高度吻合，而传统方法很快偏离为不可能预测。相关数据已免费开放，论文发表于 PNAS。

`MIT News（RSS）`


---

**8. [Google 与 Johns Hopkins 论文：Pro² Agent 用问题状态追踪提升 MLE-Bench 成绩](https://x.com/rohanpaul_ai/status/2123866338850709801)**

> 　Google 与 Johns Hopkins 的论文 Pro² Agent 提出，让 AI 研究智能体先构建显式 Problem State，记录疑似瓶颈、文献候选修复和置信度，再通过单变量实验更新信念，而不是只循环改代码保留最高分。

`X：Rohan Paul (@rohanpaul_ai)`


---

**9. [OpenAI 研究对抗模型蒸馏](https://x.com/OpenAI/status/2123862344422088794)**

> 　知识蒸馏可以复制强大的 AI 能力，却无法复制围绕这些能力构建的安全防护措施。

我们分享了一项新研究，介绍我们在打击针对自家模型的蒸馏方面所做的工作、这些能力如何迁移，以及我们如何检测并阻断协同性的尝试。

这些发现正帮助我们强化防御，并支持全行业的安全防护。

https://openai.com/index/combatting-adversarial-distillation/

`X：OpenAI (@OpenAI)`


---

**10. [Stanford 等机构论文：27B 开源模型可无训练自行改写权重](https://x.com/rohanpaul_ai/status/2123828039276773655)**

> 　Stanford、UIUC 等机构的论文提出自改写方法，Qwen3.5-27B 在梯度被封锁的条件下，比较答完题与耗尽 token 答案的隐藏状态并削弱分离两者的方向，自行改写权重。该改动使 490 道未见题目的准确率从 57.2% 升至 63.8%，测试提前固定；2B 模型未做改动，4B 和 9B 模型则改坏了自身。

`X：Rohan Paul (@rohanpaul_ai)`


---

> 📖 更多内容请访问 [ai-daily](https://miaohua1982.github.io/ai-daily/)