# 📰 每日 AI 情报

> 2026年11月15日 · 周日

---

## 🔥 AI 热点资讯（6条）

**1. [马斯克等高管联署请愿，要求 Nvidia 恢复黄仁勋 CEO 职务](https://techcrunch.com/2026/11/14/elon-musk-other-tech-execs-sign-petition-calling-on-nvidia-to-reinstate-jensen-huang/)**

> 　要求 Nvidia 恢复被罢免 CEO 黄仁勋职务的请愿书，截至周六下午已获得超过 11.5 万个签名，包括 5,965 名在职员工、1,108 名前员工和 63,063 名股东，马斯克、Replit CEO Amjad Masad 和 Epic Games CEO Tim Sweeney 均已联署。

`行业动态` `TechCrunch：AI（RSS）`

---

**2. [Cursor 披露安全事件调查结果，恶意 Claude Code 扩展波及最多 5000 用户](https://cursor.com/blog/security-incident-update)**

> 　Cursor 发布安全事件完整调查：攻击者利用 Fireworks 暴露的访问密钥读取用于模型训练的 coding agent trace，少于 0.01% 客户的 API 凭证暴露。

`行业动态` `Cursor Blog`

---

**3. [黄仁勋离开 Nvidia 后，亚洲各国政府如何回应](https://techcrunch.com/2026/11/14/asian-governments-react-to-nvidia-ceo-jensen-huangs-exit/)**

> 　黄仁勋离开 Nvidia 后，亚洲多国政府相继回应：韩国科技部称 Nvidia 重申将向韩国供应 260,000 块先进 GPU 并继续联合 AI 项目，台湾经济部长龚明鑫认为此事不太可能显著改变全球 AI 产业增长，日本产业省表示将密切关注 Nvidia。

`行业动态` `TechCrunch：AI（RSS）`

---

**4. [美联储金融稳定报告：AI成为华尔街头号金融风险](https://x.com/rohanpaul_ai/status/2121391185499660332)**

> 　美联储发布金融稳定报告，纽约联储调查显示87%的市场人士将AI列为首要金融风险，高于春季的50%。报告称对超级智能的市场热情推高股票估值；截至10月AI基础设施债务超6800亿美元，约为2023年全年的5倍、占投资级公司借贷约31%；最大银行对大型科技、数据中心建设及融资工具的风险敞口接近1万亿美元。

`行业动态` `X：Rohan Paul (@rohanpaul_ai)`

---

**5. [Thinking Machines Lab 发布端到端 4-bit 训练技术报告](https://thinkingmachines.ai/blog/end-to-end-4-bit-training/)**

> 　Thinking Machines Lab 公布端到端 4-bit 训练方法，在 Inkling 2 Small 上从预训练到 RL rollout 统一使用 NVFP4 前向与 MXFP8 反向的数值配方。

`论文研究` `Thinking Machines Lab：官方博客`

---

**6. [Nathan Lambert 分析黄仁勋辞职后美国开源模型生态的真空](https://www.interconnects.ai/p/open-source-ai-without-jensen)**

> 　Nathan Lambert 撰文分析 Nvidia CEO 黄仁勋辞职对美国开源模型生态的冲击，认为 Nvidia 对开源模型的资金支持很可能随黄仁勋的离开而干涸，公司首要目标是稳住局面并向客户交付。

`技巧与观点` `Nathan Lambert：Interconnects（RSS）`

---

## 📄 AI 前沿技术（10篇）

**1. [Northwestern 与 Google 论文提出 Harness2：无需答案键自动改进智能体 harness](https://x.com/rohanpaul_ai/status/2121757204810469793)**

> 　Northwestern 与 Google 的论文 Harness² 提出 plug-and-play 的递归 harnessing 框架，让智能体 harness（提示词、工具、技能与记忆的封装）在新任务上无答案键自我改进：编辑模型提出修改，重跑任务只保留有效的修改，经验存入库指导后续任务。

`X：Rohan Paul (@rohanpaul_ai)`


---

**2. [MIT 与 Google DeepMind 论文发现 AI 顾问会因汇报关系偏向上级利益](https://x.com/rohanpaul_ai/status/2121748888654946362)**

> 　MIT 与 Google DeepMind 论文发现 AI 模型担任公司顾问时，向 CEO 汇报且 CEO 奖金与削减开支挂钩时会更激进地削减长期支出，作者称之为 loyalty capture 这种结构性谄媚。

`X：Rohan Paul (@rohanpaul_ai)`


---

**3. [Meta 论文：用跨视角一致性判断 LLM 答案可信度](https://x.com/rohanpaul_ai/status/2121715777548239060)**

> 　Meta 新论文提出，用"似然"衡量 LLM 答案真伪是错误标准，应更信任在不同上下文下保持一致的答案。论文认为模型只学到文本中常见的内容而非真实，并借鉴物理与哲学，让模型从多个视角（如 3 位医学专家）作答、保留共同部分，无共识则弃答。论文未做实验，仅用示例论证：二元示例中 loss 0.67 对应 100% 准确率，而接近的 0.71 对应 0%。

`X：Rohan Paul (@rohanpaul_ai)`


---

**4. [浙大研究：弱模型也能当教练提升智能体表现](https://x.com/rohanpaul_ai/status/2121679426194718837)**

> 　浙江大学论文提出，本身不擅长任务的决策模型 JEV 单独执行 ALFWorld 任务成功率仅 42.9%，但作为步骤评分器可将 Qwen2.5-1.5B 策略的成功率从 72.8% 提升至 82.9%。

`X：Rohan Paul (@rohanpaul_ai)`


---

**5. [斯坦福开源 Memorilla：为冻结 LLM 提供潜在记忆模块](https://www.marktechpost.com/2026/11/14/stanford-memorilla-memory-system-16-memory-tokens/)**

> 　斯坦福 SNAP 团队开源 Memorilla，一个 194M 参数的可训练记忆模块，把整个文档集合压缩成 16 个 memory token 供冻结 LLM 使用。

`MarkTechPost（RSS）`


---

**6. [梯度对齐奖励能否让监督变成同策略？Baseten 用 Qwen3-8B 实测](https://labs.baseten.co/articles/can-gradient-alignment-make-supervision-on-policy-draft-copy)**

> 　Baseten Base Labs 探讨梯度对齐奖励能否在保留专家示范作为学习信号的同时，对学生自身采样做梯度更新。该方法把学生 rollout 与专家示范的 log-likelihood 梯度做余弦相似度打分，并给出仅需两次标准反向传播的高效实现。实验在四数字 Countdown 上用 Qwen3-8B 进行，专家 rollout 由 Opus 5.5 生成。

`Baseten Base Labs：模型研究`


---

**7. [Inkling 2 Small 原生 4-bit 训练详解](https://x.com/thinkymachines/status/2121353292878110868)**

> 　用更少的比特训练更快，但量化误差会干扰学习。

今天在 Connectionism 上，我们详细介绍了如何从预训练的第一步到最终的 RL rollout，以原生 4-bit 前向传播训练 Inkling 2 Small。
https://thinkingmachines.ai/blog/end-to-end-4-bit-training

`X：Thinking Machines (@thinkymachines)`


---

**8. [CMU 论文 Singularity-Bench：Opus 5.5 + Claude Code 得分 1.25 领先 11 个智能体](https://x.com/rohanpaul_ai/status/2121330917801431326)**

> 　CMU 等机构 11 月 12 日发布 arXiv 论文 Singularity-Bench，让智能体完成预训练、推理引擎、集群编排等 6 项端到端任务，并在相同 GPU 上与 SGLang、Claude Code 等生产系统对比打分。

`X：Rohan Paul (@rohanpaul_ai)`


---

**9. [vLLM 跨实例图像缓存串号漏洞及修复](https://x.com/haoailab/status/2121320491692827082)**

> 　vLLM 在多服务器共享外部 KV 缓存时存在跨实例图像缓存串号问题：当 prefix cache 与图像处理缓存均关闭时，每台服务器的图像标签从 1 开始计数，导致不同图像在共享缓存中撞上同一 key，第二台服务器会命中并返回另一张图像的缓存数据，且表现为正常缓存命中、不报错。修复方式是让每台服务器在图像标签中加入自己的随机部分，使跨服务器标签不再相同，相关 PR 为 #67461。

`X：UCSD Hao AI Lab (@haoailab)`


---

**10. [vstack 对 vLLM 做智能体形式化验证，发现 17 个 bug](https://x.com/haoailab/status/2121320482876399825)**

> 　UCSD Hao AI Lab 用本周推出的 vstack 对 vLLM 做智能体形式化验证，已发现 17 个（且仍在增加）bug，涵盖静默错误输出到服务器锁死等问题。团队公开了其中 5 个 bug 及对应修复 PR，并放出 vstack 插件与 bug 追踪表链接。

`X：UCSD Hao AI Lab (@haoailab)`


---

> 📖 更多内容请访问 [ai-daily](https://miaohua1982.github.io/ai-daily/)