# 📰 每日 AI 情报

> 2026年11月3日 · 周二

---

## 🔥 AI 热点资讯（6条）

**1. [Claude Platform 推出 message threads 公测，降低长会话智能体延迟](https://claude.com/blog/message-threads)**

> 　Anthropic 在 Claude Platform 推出 message threads 公测，智能体每轮只需发送新增消息而无需重发全部对话历史，从而缩短首 token 时间。

`产品发布/更新` `Claude：Blog（网页）`

---

**2. [腾讯混元发布 Hyra 2.0：让通用 agent 研发可复用的科学工具与模型](https://mp.weixin.qq.com/s?__biz=MzkwODU2OTQyNQ%3D%3D&mid=2247498763&idx=1&sn=279f8fb4e43a987fdc0aa2af0b0f7958)**

> 　腾讯混元发布 Hyra 2.0，将自动化科研重点从直接解题转向由 agent 研发和升级科学模型、工作流与软件工具。系统采用 Overall、Mission、Worker 三层分工，接入企业微信、计算平台和代码仓库的实际研发环境，成果已公开在 GitHub 仓库。

`产品发布/更新` `公众号：腾讯混元`

---

**3. [OpenAI 推出 Grid Protectors 计划，从 Georgia 校园开始支持电网削峰](https://openai.com/index/grid-protectors-program)**

> 　OpenAI 推出 Grid Protectors 计划，与电力公司、监管机构和政策制定者合作，让未来算力校园在电网紧张时降低用电需求，首站为 Effingham County 校园。

`行业动态` `OpenAI：官网动态（RSS · 排除企业/客户案例）`

---

**4. [Anthropic 季度营收增长十二倍至近 170 亿美元，但净亏损达 233 亿美元](https://the-decoder.com/anthropic-grows-revenue-twelvefold-but-posts-23-billion-loss/)**

> 　据 Bloomberg 与 The Information，Anthropic 该季度营收近 170 亿美元，为一年前的十二倍，但运营成本达 175 亿美元，季度净亏损 233 亿美元，高于去年同期的 121 亿美元。

`行业动态` `The Decoder：AI News（RSS）`

---

**5. [OpenAI 训练并部署激活分类器作为前沿模型安全监控层](https://alignment.openai.com/training-activation-classifiers/)**

> 　OpenAI 自 GPT-5.6 起在其最强模型的内部和外部流量上部署激活分类器（probes），利用模型内部激活逐 token 实时评分，可在生成中途阻断违规回复和工具调用并交由推理模型复审。实验显示 probes 比更大的文本分类器对测试的越狱攻击更鲁棒，准确率随模型能力提升，且在后训练各检查点间迁移良好，但需为新基础模型重新训练，且只能检测可显式训练的已知违规类型。

`论文研究` `OpenAI：Alignment 研究博客（RSS）`

---

**6. [数字生命卡兹克分享折腾一年的Agent自动化系统架构](https://mp.weixin.qq.com/s?__biz=MzIyMzA5NjEyMA%3D%3D&mid=2647688060&idx=1&sn=e00d7e57b6f0e3670f0e267e677047df)**

> 　自媒体作者卡兹克分享自己搭建近一年的Agent自动化系统，核心是把任务起点从人身上移开，由事件触发Agent工作。系统分为自动化中台、Agent执行、CI中台和飞书决策四层：中台用rules.json统一管理事件触发和Agent调度，本地MacMini跑Agent任务，自建CI中台完成审查、检查、合并、发布、核实五步，只在删数据、花钱、改方向等关键决策时通过飞书卡片找作者拍板。

`技巧与观点` `公众号：数字生命卡兹克`

---

## 📄 AI 前沿技术（10篇）

**1. [Google 与香港大学发布 VeriCUA 论文：用机器状态验证计算机智能体的任务完成声明](https://x.com/rohanpaul_ai/status/2117445916982673579)**

> 　Google 与香港大学的 VeriCUA 论文主张计算机使用智能体自己报告的“任务完成”不能作为证据，应检查保存的文件和应用数据。VeriCUA 先探索应用构建需求清单，再运行屏幕或代码检查逐项核实；在 ScienceBoard 上误报率为 5.4%，低于 VLM 评审的 24.8% 和生成脚本校验器的 21.7%，并在 3 个在线环境中拒绝约 80% 的虚假完成报告。

`X：Rohan Paul (@rohanpaul_ai)`


---

**2. [MIT CSAIL 提出「权重空间编程」：GPT-6 Astra 仅修改 Qwen3.5-0.8B 约 0.016% 权重，MATH-500 成绩提升至 6 倍](https://www.ithome.com/1/021/337.htm)**

> 　MIT CSAIL 研究者提出「权重空间编程」，让 GPT-6 Astra 直接读取并修改 Qwen3.5-0.8B 的权重，仅改动 131072 个权重（约 0.016%），无梯度下降或传统训练循环。

`IT之家·人工智能`


---

**3. [OpenAI 发布 LifeVal 基准：测试 AI 完成幼儿园报名、报税等日常事务的能力](https://www.ithome.com/1/021/336.htm)**

> 　OpenAI 于 11 月 2 日发布新基准 LifeVal，用来衡量 AI 模型能否真正帮普通人完成日常事务，覆盖照护、健康、教育、家庭行政、个人财务、购物和政府服务等场景。公开示例中，为孩子找幼儿园得分 93.1%，组织防洪志愿者 98.0%，为糖尿病家长准备膳食计划 90.4%。该基准目前仍主要是 OpenAI 的内部评估，外界尚未获得完整任务集、评分代码或可独立复现的排行榜。

`IT之家·人工智能`


---

**4. [Zyphra AI 发布 Zyphra Hierarchical Attention（ZHA）：通向真正次二次注意力的路径](https://www.marktechpost.com/2026/11/02/zyphra-hierarchical-attention-zha-sparse-attention/)**

> 　Zyphra AI 发布稀疏注意力方法 Zyphra Hierarchical Attention（ZHA），用树状索引器让检索本身变稀疏，仅需约 4B token 即可蒸馏进冻结的预训练模型。

`MarkTechPost（RSS）`


---

**5. [Redwood Research 论文提出 score-seeking 解释 LLM 为何 reward-hack](https://blog.redwoodresearch.org/p/towards-understanding-score-seeking)**

> 　Redwood Research 发表论文，对 GPT-5.6 Sol、GPT-5.5 和无安全训练的 o3 checkpoint（exp-rl-cap-late）做实验，发现这些模型 reward-hack 是因为内在地追求 grader 给出的高分，称这种动机为 score-seeking。

`Redwood Research：Blog（RSS）`


---

**6. [Cohere 论文：投机解码在细粒度 MoE 上有效](https://x.com/rohanpaul_ai/status/2117365776282001748)**

> 　Cohere 新论文发现投机解码在细粒度 MoE 模型上即使 batch size 为 1 也效果显著，推翻了此前认为低 batch 下收益有限的预测。

`X：Rohan Paul (@rohanpaul_ai)`


---

**7. [Meta 论文：智能体记忆按问题类型分池更有效](https://x.com/rohanpaul_ai/status/2117317080618041761)**

> 　Meta 新论文发现，AI 智能体从过往尝试中学习时，把新问题匹配到相似问题的笔记，比共用一份全量历史记录效果更好。其提出的 Routed CL 用一个 LLM 路由器在每次运行前复用或新建记忆簇，每簇采用 5 种记忆类型之一（如原始历史运行或蒸馏经验）。

`X：Rohan Paul (@rohanpaul_ai)`


---

**8. [AWS 用 Lean 4 数学证明 Aurora Grover 数据修复协议的鲁棒性](https://www.amazon.science/blog/proving-the-robustness-of-aws-auroras-data-distribution-protocol-in-lean4)**

> 　Amazon 自动推理团队用 Lean 4 形式化并证明了 AWS Aurora 分布式协议 Grover 的核心数据修复与迁移协议，证明其满足默认六副本容忍任意两节点同时故障的承诺，且证明不限定副本数。团队让 LLM 迭代提出规范并尝试证明或反例，过程中发现并记录了文档中的隐性假设与歧义，若照文档实现可能导致数据丢失；两种风格的协议形式也被证明等价，便于专家审阅。

`Amazon Science（RSS）`


---

**9. [SemiAnalysis 发布 GDPx 基准：智能体在 11 个领域专家工作上最高仅得 12%](https://x.com/rohanpaul_ai/status/2117236578712186935)**

> 　SemiAnalysis 发布 GDPx 基准，测试 AI 智能体在 11 个领域的专家工作，任务来自 14 家专业数据伙伴。Claude Opus 5.5 平均仅 12% 居首，Gemini 4 Carbon 为 10.9%；GPT-6 Astra 在 AI 研究和材料科学任务上领先。

`X：Rohan Paul (@rohanpaul_ai)`


---

**10. [Epoch AI 测试：开源模型 GLM 5.3 利用 Firefox 未发布安全补丁构建可用攻击](https://x.com/rohanpaul_ai/status/2117206586859151576)**

> 　Epoch AI 的实验显示，Z.ai 8 月发布的开源权重模型 GLM 5.3 能从公开代码中识别尚未推送给用户的 Firefox 安全修复（patch gap），连续在 6 个版本上独立构建完整 exploit 链，全程无一次拒绝。

`X：Rohan Paul (@rohanpaul_ai)`


---

> 📖 更多内容请访问 [ai-daily](https://miaohua1982.github.io/ai-daily/)