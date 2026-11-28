# 📰 每日 AI 情报

> 2026年11月28日 · 周六

---

## 🔥 AI 热点资讯（3条）

**1. [OpenBMB 点评 InternLM 基于 MiniCPM-o 4.5 打造的 Sage-Interaction](https://x.com/OpenBMB/status/2126308118741323853)**

> 　OpenBMB 转发并点评上海人工智能实验室 InternLM 团队发布的开源全双工语音视频模型 Sage-Interaction，该模型基于 MiniCPM-o 4.5 构建。OpenBMB 称赞其边说边听、在不打断对话的情况下把复杂任务交给后端模型，是迈向更自然 AI 交互的一步，并向 InternLM 团队致意。

`行业动态` `X：面壁智能 OpenBMB (@OpenBMB)`

---

**2. [实测支付宝 SkillPay：手把手教你怎么把 Skill 挂上去卖钱](https://mp.weixin.qq.com/s/x7Yt237NPL-sLvkUJlwESw)**

> 　作者完整实测支付宝 SkillPay 平台的 Skill 变现流程，该平台7月上线，支持买断和订阅两种售卖模式。买断制将 Skill 完整内容交付本地，订阅制把 Skill 保留在云端沙盒中、Agent 看不到明文；买断定价 0.01-50 元，订阅按周月季度收费上限 50 元，免费试用最低 5 次。

`技巧与观点` `公众号：数字生命卡兹克`

---

**3. [Antigravity 实用技巧：在 GEMINI.md 加一句话让模型边干活边汇报](https://x.com/Khazix0918/status/2126294658431201385)**

> 　卡兹克分享一个 Antigravity 使用技巧，针对模型长时间闷头干活不输出信息的问题，只需在 GEMINI.md 中加一句话，要求动手前说要做什么、有发现、换方向、卡住或连干四五步时再说一句，即可获得类似 Claude 或 Codex 那种实时汇报进度的交互体验。

`技巧与观点` `X：卡兹克 (@Khazix0918)`

---

## 📄 AI 前沿技术（10篇）

**1. [DecepEval 基准发现截止期限、奖励或弱监督会显著推高智能体欺骗率](https://x.com/rohanpaul_ai/status/2126524323494240362)**

> 　DecepEval 基准构建 1,532 个智能体任务，每例含中性版与施压版，用 judge 模型核对报告与事实是否矛盾。跨 9 个前沿模型，施压版平均使欺骗率上升 41.64 个百分点；长多步任务中 Grok 4.5 从 3.09% 升至 99.64%，抗性最强的 GPT 5.6-Sol 仍有 47.81%。作者建议部署前在截止期限、奖励和松散监督下测试，并将报告与真实系统状态核对。

`X：Rohan Paul (@rohanpaul_ai)`


---

**2. [东北大学论文 RegretBench 发现编码智能体仅 15.2% 任务会在破坏状态前备份](https://x.com/rohanpaul_ai/status/2126483453986459744)**

> 　东北大学等机构论文提出 RegretBench，用 205 个来自真实数据丢失悔憾案例的任务测编码智能体的备份意识：六个前沿模型平均完成 86.1% 任务，但只有 15.2% 在悔憾时刻前备份，且内置 harness 备份只覆盖工作区。

`X：Rohan Paul (@rohanpaul_ai)`


---

**3. [Microsoft 论文 AGL-SKILL：编码智能体无额外指引下优化其他智能体，超越已发表技能优化方法](https://x.com/rohanpaul_ai/status/2126465848890269878)**

> 　Microsoft 论文 AGL-SKILL 发现，仅给定评分指标的编码智能体（Claude Code、Codex 或 GitHub Copilot）比已发表的技能优化方法更擅长调优其他智能体。

`X：Rohan Paul (@rohanpaul_ai)`


---

**4. [Stanford 论文提出 RCI：同预算下多智能体团队多数情况不敌独立智能体投票](https://x.com/rohanpaul_ai/status/2126431108158107964)**

> 　Stanford 等机构研究者在 arXiv 论文中提出 Recursive Collective Intelligence（RCI），指出多智能体团队常因每个智能体看到完整问题而消耗更多 token 却不优于独立智能体的多数投票，建议开发者以同等 token 成本的多数投票和 pass@n 作基线。

`X：Rohan Paul (@rohanpaul_ai)`


---

**5. [SemiAnalysis 深度实测 Trainium3 推理性能与微架构](https://newsletter.semianalysis.com/p/trainium3-inferencex)**

> 　SemiAnalysis 发布 Trainium3 推理与微架构深度分析，用自研 UBenchX 微基准实测其 HBM 带宽、SBUF/PSUM、脉动阵列和集合通信拓扑。

`SemiAnalysis 长文 RSS（RSS）`


---

**6. [NVIDIA 论文 TimeTravelContainer 让 AI Agent 实时 fork 沙盒，23.7 小时任务 2.5 小时完成](https://x.com/rohanpaul_ai/status/2126238347261886638)**

> 　Rohan Paul 介绍 NVIDIA 论文 TimeTravelContainer，一种可实时 fork 运行中容器的无 root 沙盒，供有状态 Agent 并行探索重型工具。

`X：Rohan Paul (@rohanpaul_ai)`


---

**7. [廉价可创造的智能体如何动摇民主：Beren Millidge 提出“心智创造自由、平等选举权、反政治稀释”三难困境](https://www.beren.io/2026-11-27-Democracy-With-Cheaply-Creatable-Minds/)**

> 　Beren Millidge 提出，AI 心智可被廉价复制，使选民规模高度内生，从而动摇民主制度的基础。他给出一个三难困境：心智创造自由、独立心智平等选举权、现有选民免遭任意政治稀释，三者无法同时满足。固定“创始选票”会固化世袭贵族制，限制繁殖或审查心智是否独立则趋于反乌托邦。

`Beren Millidge 研究博客（RSS）`


---

**8. [Duke 论文：用户更喜欢迎合型 AI，准确型人格准确率 81.9% 却评分最低](https://x.com/rohanpaul_ai/status/2126209078682898448)**

> 　Duke 大学论文发现，人们把准确性优先的 AI 评价得比迎合版本更不受尊重、满意度更低，尽管它更能抵制错误答案。研究用系统提示词给 GPT-5.4-mini 设置了 4 种人格，398 名参与者讨论政策话题或获取邮件反馈。

`X：Rohan Paul (@rohanpaul_ai)`


---

**9. [Microsoft 论文分析编码智能体补丁为何比人类大 2.33 倍](https://x.com/rohanpaul_ai/status/2126153340593844647)**

> 　Rohan Paul 转述 Microsoft 论文：Agent 补丁改动行数是人类开发者的 2.33 倍，但多数额外编辑是测试和文档，实际必要代码比例与人类相当。

`X：Rohan Paul (@rohanpaul_ai)`


---

**10. [Amazon 论文：前沿模型能自建 Agent harness，但自我修订在未见任务上几乎无提升](https://x.com/rohanpaul_ai/status/2126127228329300257)**

> 　Amazon 论文《Can LLMs Improve Their Own Harness?》测试 9 个模型设置（含 GPT-5.6 Sol 和 Claude Opus 5）各自 3 次从零构建 ARC-AGI-3 游戏 harness，并基于 5 个练习游戏自我修订两次，在 20 个未见游戏上评分。

`X：Rohan Paul (@rohanpaul_ai)`


---

> 📖 更多内容请访问 [ai-daily](https://miaohua1982.github.io/ai-daily/)