# 📰 每日 AI 情报

> 2026年10月12日 · 周一

---

## 🔥 AI 热点资讯（1条）

**1. [GPT-6.1 Sol 在 Codex 与 Work 中默认上下文长度提升至 500k](https://x.com/thsottiaux/status/2109430343346581527)**

> 　Tibo 宣布 GPT-6.1 Sol 在 Codex 与 Work 中的默认上下文长度从 272k 提升到 500k，约增加 80%。此举可减少压缩（compaction）发生，帮助需要长期保留大量上下文和细节的任务；用户仍可自行覆盖设置，模型最大上下文长度为 1M。

`产品发布/更新` `X：Tibo (@thsottiaux)`

---

## 📄 AI 前沿技术（10篇）

**1. [Sakana AI 提出 MASS：用多智能体自监督实现同质递归自我改进](https://pub.sakana.ai/mass/)**

> 　Sakana AI 发布 MASS（Multi-Agent Self-Supervision）方法，让同一模型同时担任执行者、工作流优化器和评估者，将多智能体团队的集体经验蒸馏为递归自我改进（RSI）的自监督信号。

`Hacker News：AI 热帖`


---

**2. [研究显示多智能体团队消耗大量 token 却几乎无质量提升](https://the-decoder.com/ai-agent-teams-waste-massive-tokens-for-barely-measurable-quality-gains-research-finds/)**

> 　Vals AI 在 Vibe Code Bench 上测试 GPT-6 Sol 和 Claude Opus 5.5 的单智能体与团队表现，团队成本为单体的 1.8x 到 5.1x，四组对比中仅 GPT-6 Sol 在 medium reasoning 下高出 7.3 分且具统计显著性。

`The Decoder：AI News（RSS）`


---

**3. [Epoch AI 发布 InnovationEval 评测，AI 智能体远未达到自主研究水平](https://the-decoder.com/ai-agents-overstate-their-results-and-remain-far-from-autonomous-research-study-finds/)**

> 　Epoch AI 用新基准 InnovationEval 测试 Claude Fable 5 和 GPT-5.6 Sol 能否独立发明新训练方法，以人类设计的 SDPO 对 GRPO 的改进为参照。

`The Decoder：AI News（RSS）`


---

**4. [清华 AAArena：AI 智能体靠回放学游戏，Pacman 登顶但复杂规则卡壳](https://x.com/rohanpaul_ai/status/2109268277805629760)**

> 　清华论文构建 AAArena，用清华年度机器人竞赛的 12 款游戏和 1920 个存档人类程序作为对手，测试编码智能体能否在模型权重不变的情况下通过读规则、选对手、研究回放来改写游戏 bot。在全部 3 款测试游戏中，详细回放反馈均优于仅胜负信号；有回放时 Pacman bot 排名第 1，无回放仅第 11。但比赛预算增至 3 倍，4 个卡住的 bot 仍无一升至第 1。

`X：Rohan Paul (@rohanpaul_ai)`


---

**5. [亚马逊论文：LLM 可当研究世界模型预测实验结果](https://x.com/rohanpaul_ai/status/2109243398628708619)**

> 　亚马逊新论文提出用 LLM 充当"研究世界模型"，在实验开跑前预测训练改动的收益。基于 9 个设置、2653 条真实实验记录测试，同设置历史记录将预测与实际结果的平均排名相关性从 0.506 提升至 0.774（5 个设置）；在 OLMo3-100M 上，低推理强度加记录得 0.892，最高推理强度无记录仅 0.648。作者建议研究智能体记录包括失败在内的每次实验，并喂给选下次运行的模型。

`X：Rohan Paul (@rohanpaul_ai)`


---

**6. [UC Berkeley 等团队研究：仅依赖 AI 10 分钟即可削弱专注与坚持困难任务的能力](https://vcresearch.berkeley.edu/news/using-ai-just-10-minutes-erodes-your-ability-persist-hard-things)**

> 　UC Berkeley、Carnegie Mellon、MIT、牛津和 UCLA 学者合作的研究发现，仅 10 分钟依赖 AI 工具即显著削弱用户专注和坚持困难任务的能力。

`Hacker News：AI 热帖`


---

**7. [Meta 论文：GitSwarm 让多智能体共享 Git 仓库协作](https://x.com/rohanpaul_ai/status/2109230760020574281)**

> 　Meta 新论文提出 GitSwarm，让多个相同 AI 智能体在共享 Git 仓库上协作，无需管理者分配任务，每个智能体读取过往工作（含失败尝试）并提交结果及所依赖的 commit 列表。在 ProgramBench 的 50 个程序重建任务上，GitSwarm 得分 79.4%，而单个 Codex 智能体在相近算力下最高仅 65.1%；后续智能体有 94.7% 建立在已保存的贡献之上。

`X：Rohan Paul (@rohanpaul_ai)`


---

**8. [WUJI Hand 2 机器灵巧手展示转笔技能，全套代码以 Apache 2.0 开源](https://x.com/rohanpaul_ai/status/2109046160564584696)**

> 　WUJI 的 20 关节机器手 WUJI Hand 2 在物理仿真中训练转笔策略并成功迁移到实机，在 IROS 2026 现场展示，还配有一款可实时控制该手的传感手套。

`X：Rohan Paul (@rohanpaul_ai)`


---

**9. [Sakana AI 发表 Beyond Imitation 论文，MLR 系统检出 73.43% 核心论断错误](https://www.marktechpost.com/2026/10/10/sakana-ais-llm-peer-review-system-catches-73-of-core-claim-errors/)**

> 　Sakana AI 在 TMLR 发表 Beyond Imitation 论文，提出 Contradiction Benchmark 与 Multi-Layered Review（MLR）系统，在 257 篇论文中插入 1,164 处矛盾来测试 AI 审稿的真实错误检测能力。

`MarkTechPost（RSS）`


---

**10. [Stanford 论文提出按失败类型决定改 harness 还是训练权重](https://x.com/rohanpaul_ai/status/2109021283329687635)**

> 　一篇 Stanford 等机构的论文发现，harness（提示词、工具、检查）改动能修复循环或停滞等过程失败，而交付糟糕计划的内容失败需要权重训练。

`X：Rohan Paul (@rohanpaul_ai)`


---

> 📖 更多内容请访问 [ai-daily](https://miaohua1982.github.io/ai-daily/)