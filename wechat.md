# 📰 每日 AI 情报

> 2026年10月13日 · 周二

---

## 🔥 AI 热点资讯（10条）

**1. [Meta 发布 Muse Wonder 和 Muse Wonder Full，Artificial Analysis 实测智能水平较前代显著提升](https://artificialanalysis.ai/articles/muse-wonder)**

> 　Meta 发布 Muse Wonder 和 Muse Wonder Full 两款模型，在 Artificial Analysis Intelligence Index v4.3 上分别得 52 和 56 分（max reasoning effort）。

`模型发布/更新` `Artificial Analysis 完整文章（网页）`

---

**2. [xAI 推出 The X Subscription 整合 Grok、Grok Bot、Cursor 与 X Premium](https://x.ai/news/x-subscription)**

> 　xAI 推出 The X Subscription 订阅，将 Grok、Grok Bot、Cursor 和 X Premium 合入一个计划，未来几天内向全球用户开放。

`产品发布/更新` `xAI：News（网页）`

---

**3. [微软发布自研芯片 Maia 300 并将大规模扩展 Maia 推理部署](https://x.com/satyanadella/status/2109631106404487523)**

> 　微软宣布明年起将 Maia 芯片家族扩展到多吉瓦级部署，作为自家产品和服务的首选推理系统，并发布 Maia 300，每瓦 token 产出比主流 GPU 系统高 40%。Maia 200 已在美国、欧洲和澳大利亚部署，在 Teams 和 Copilot 场景中每瓦 token 产出提升最高 1.7x。

`产品发布/更新` `X：Satya Nadella (@satyanadella)`

---

**4. [Epic Games 转向 AI 先行开发模式，与迪士尼合作射击游戏无限期延期](https://arstechnica.com/gaming/2026/10/report-epic-games-goes-all-in-on-ai-for-disney-collaboration/)**

> 　据 Bloomberg 报道，Epic Games 在与迪士尼 15 亿美元合作项目中转向 AI 先行开发，由 Anthropic 的 Claude 等模型编写全部代码并指导全部美术，人类开发者负责管理和引导生成内容。

`行业动态` `Ars Technica：AI（RSS）`

---

**5. [QGIS 通过 QEP428 禁止 AI 辅助贡献](https://github.com/qgis/QGIS-Enhancement-Proposals/pull/387)**

> 　QGIS 通过 QEP428 提案，将 AI 政策改为严格的 NOT ALLOWED，由 nyalldawson 提交并于 2026 年 10 月 7 日合并进 QGIS-Enhancement-Proposals 仓库。

`行业动态` `Hacker News：AI 热帖`

---

**6. [用户报告 Codex CLI 0.157.0 默认启动持久化自更新后台守护进程](https://github.com/openai/codex/issues/48195)**

> 　一位 Linux (WSL2) 用户报告，Codex CLI 0.157.0 起打开交互式会话即默认启动持久后台守护进程 codex app-server --managed-daemon，窗口关闭后仍驻留。

`行业动态` `Codex：GitHub Releases（RSS）`

---

**7. [Anthropic 研究：小型 AI 模型可能接近在 IoT 设备上自主复制](https://www.anthropic.com/research/self-replicating-ai)**

> 　Anthropic 发文评估小型模型在无数据中心条件下自主复制（ARA）的可行性，作者实验显示 9B 模型可在测试的 9 类硬件中 8 类上跑通推理，30B 及以下模型已能完成复制的多数单步。

`论文研究` `Anthropic：Research（发表成果 · 网页）`

---

**8. [AlphaProof Nexus 攻克 9 个未解 Erdős 问题并经同行评审](https://the-decoder.com/google-deepminds-alphaproof-nexus-solved-dozens-of-open-math-problems-and-actually-got-peer-reviewed/)**

> 　Science 新研究显示，Google DeepMind 的 AlphaProof Nexus 独立解决了 353 个开放 Erdős 问题中的 9 个，其中 2 个悬置 56 年。

`论文研究` `The Decoder：AI News（RSS）`

---

**9. [Vapi 自研代码审查机器人如何将 PR 合并时间缩短一半](https://vapi.ai/blog/ai-code-review-bot)**

> 　Vapi 工程师 Lat Ware 自研 Pedantic Review Bot，使 PR 从开到合并的平均时间从 130 多小时降到 65 小时。机器人会运行测试和小复现来验证发现，分析和发评论分属两个 job，只能评论不能批准或推送；2026 年 9 月 2 日至 10 月 2 日审查了 1,694 个 PR，在 276 个中提出 363 个 blocker 发现。

`技巧与观点` `Vapi 产品与 Agent 方法`

---

**10. [用 Claude Opus 5.5、Blender、Unreal Engine 和 Meshy 构建游戏的七步教程](https://x.com/MeshyAI/status/2109550836934471864)**

> 　一篇教程介绍用 Claude Opus 5.5 配合 Claude Code、Blender、Unreal Engine 5 和 Meshy 构建游戏的方法。核心思路是给每个工具分配单一职责：通过 MCP 连接 Blender 和 Meshy，由 Meshy 生成道具和角色、Blender 清理和放置、Unreal 负责光照物理和游戏本身、Opus 在一个对话里调度三者。流程为先让 Opus 头脑风暴 5 个游戏点子再展开，告知 GPU 以便压满画面性能，首个完整构建约花 4 小时和约 19% 的每周 Max plan 用量，之后因素材复用会快很多。

`技巧与观点` `X：Meshy (@MeshyAI)`

---

## 📄 AI 前沿技术（10篇）

**1. [9 年前英伟达 Tesla V100 老将再战：4 GPU 集群 AI 推理跑赢 2 台 DGX Spark](https://www.ithome.com/1/012/165.htm)**

> 　YouTube 频道 Jun Yamog 测试将 4 张英伟达 Tesla V100 装于 NVLink 载板，在 4-bit 量化 Qwen3.8-Flash-Next 基准中长提示处理速度较 2 台 DGX Spark 快 40%、较 M5 Ultra 快 230%。

`IT之家·人工智能`


---

**2. [Anthropic 谈抵御蒸馏攻击进展](https://x.com/AnthropicAI/status/2109795898909950247)**

> 　过去几个月，我们在降低针对 Claude 的蒸馏攻击有效性方面取得了重大进展。

在这篇文章中，我们解释了具体做法：https://www.anthropic.com/research/distillation-defenses

`X：Anthropic (@AnthropicAI)`


---

**3. [Artificial Analysis 发布 AA-3D 基准，评测模型构建交互式 3D 场景能力](https://x.com/ArtificialAnlys/status/2109791341802885209)**

> 　Artificial Analysis 推出 AA-3D 基准，让 21 个模型作为智能体在离线沙箱中把书面简报转化为 three.js 网页，由超 1000 名评委盲评产出逾 10000 票的 Elo 排名。

`X：Artificial Analysis (@ArtificialAnlys)`


---

**4. [阿里 Qwen 推出 QwenGyre：面向超长时程智能体的弹性强化学习框架](https://www.marktechpost.com/2026/10/12/alibaba-qwen-introduces-qwengyre-elastic-reinforcement-learning-rl-for-xlong-horizon-agents/)**

> 　阿里 Qwen 团队推出 QwenGyre，一个面向超长时程智能体训练的弹性强化学习框架，通过在线 RL 在未经修改的黑盒 harness 中训练编码智能体，单次 rollout 可运行数小时、处理近 1M tokens。

`MarkTechPost（RSS）`


---

**5. [Sakana AI 与 UC Berkeley 提出 MASS 自我改进方法，能力提升但共享盲点可能让错误延续](https://the-decoder.com/sakana-ais-self-improving-model-gets-better-at-solving-and-judging-but-cant-catch-its-own-blind-spots/)**

> 　Sakana AI 与 UC Berkeley 研究者提出多智能体自我监督方法 MASS，让单个 Qwen3.6-27B 模型身兼解题、评估、优化三角色，无需更强教师模型即可递归自我改进。

`The Decoder：AI News（RSS）`


---

**6. [AWS 提出 priming 方法，可将预训练 Transformer 改造成混合状态空间架构](https://www.amazon.science/blog/can-we-change-an-ai-models-architecture-without-retraining-it-from-scratch)**

> 　AWS 团队发布论文《Priming: Hybrid state space models from pre-trained Transformers》，提出 priming 方法，复用预训练 Transformer 权重构建混合架构，将预训练成本降低逾 99%，全流程消耗不足源模型 0.5% 的 token 预算。

`Amazon Science（RSS）`


---

**7. [Meta 对比 Muse 模型分布外任务表现](https://x.com/AIatMeta/status/2109697981641351510)**

> 　为了量化模型处理陌生任务的能力，我们将后训练中训练过的任务的测试时计算扩展与其他任务进行了对比。

两个模型在分布外任务上的提升相似，但在相同的分布内得分下，Muse Wonder Full 在陌生任务上的表现优于 Muse Spark 1.3 趋势所预测的水平。我们将这一上移归因于更强的基座模型，它能更有效地将后训练带来的增益迁移到我们未曾预料到的任务上。

`X：AI at Meta (@AIatMeta)`


---

**8. [微软推出 StudentSim 评估 AI 辅导工具](https://x.com/MSFTResearch/status/2109684149674013109)**

> 　StudentSim 是一个研究系统，用于在 AI 辅导工具接受学习者测试之前对其进行评估和改进。它模拟个体可能如何与辅导工具互动，从而提供反馈以提升辅导工具在 chess、写作和数学等学科上的表现：https://msft.it/6013aS3JF

`X：Microsoft Research (@MSFTResearch)`


---

**9. [Microsoft Research 提出 Fork-and-Flush：清空聊天历史帮助 AI 智能体找到更优解](https://the-decoder.com/clearing-chat-history-helps-ai-agents-find-better-solutions/)**

> 　Microsoft Research 研究发现，长时间运行的自主研究型智能体常陷入"idea basins"，即使增加算力也难以突破。

`The Decoder：AI News（RSS）`


---

**10. [NVIDIA 论文提出在首个让测试通过的编辑处评估 base 模型，预测编码智能体后训练表现](https://x.com/rohanpaul_ai/status/2109670406257025311)**

> 　NVIDIA 论文提出，相比逐步打分，只在首个让测试通过的决定性编辑处评估 base 模型更能预测其智能体后训练潜力。方法回放成功智能体轨迹并在每次编辑后重跑测试，检查 base 模型是否会写出该编辑、在失败编辑中选中它并写出可通过的实现。模型写出该编辑的概率排序与十个模型后训练后的 SWE-bench Verified 得分相关性达 0.964，且只需基准的成功轨迹和测试即可运行。

`X：Rohan Paul (@rohanpaul_ai)`


---

> 📖 更多内容请访问 [ai-daily](https://miaohua1982.github.io/ai-daily/)