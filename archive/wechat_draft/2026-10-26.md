# 📰 每日 AI 情报

> 2026年10月26日 · 周一

---

## 📄 AI 前沿技术（10篇）

**1. [德州大学Jev-Mem让AI记忆构建提速6.6倍](https://x.com/rohanpaul_ai/status/2114363208702275807)**

> 　德州大学论文提出Jev-Mem，把链接、停止搜索等小决策交给快速打分模型Jev批量输出概率，LLM只在最后读取记忆并作答，使长对话记忆构建速度提升6.6倍。在LoCoMo长对话基准上，其回答得分0.777，高于最佳基线的0.700；记忆构建耗时158秒，最快对手为1,044秒，回答耗时0.93秒对1.47秒。

`X：Rohan Paul (@rohanpaul_ai)`


---

**2. [斯坦福与 UC Berkeley 推出 TokenGate：token 门控注意力让长上下文 prefill 最快提升 11.3 倍](https://www.marktechpost.com/2026/10/25/stanford-berkeley-tokengate-learned-token-pruning-llm-prefill/)**

> 　斯坦福和 UC Berkeley 研究者发布 TokenGate，一种给现有 LLM 加上可学习 token 剪枝的模块，在 Qwen3-1.7B 上实现 1.4x 至 11.3x 的 TTFT 加速，峰值 prefill 显存降低 1.5x 至 3.4x 且无精度损失。

`MarkTechPost（RSS）`


---

**3. [Google DeepMind 等发布 TheoPhysEval 基准，最强智能体解出 50 道未发表理论物理题中的 49 道](https://x.com/rohanpaul_ai/status/2114306498658812026)**

> 　Google DeepMind 与多所高校发布 TheoPhysEval 基准，用专家贡献的 50 道未发表研究级理论物理题测试 AI 智能体，每道题约相当于领域专家一天的工作量，单题成本低于 3 美元。

`X：Rohan Paul (@rohanpaul_ai)`


---

**4. [Anthropic 联合创始人 Jack Clark 将自我改进 AI 的预测提前到 2027 年](https://the-decoder.com/anthropic-co-founder-jack-clark-moves-his-prediction-for-self-improving-ai-forward-to-2027/)**

> 　Anthropic 联合创始人 Jack Clark 依据新基准 TasteVal 的结果，将递归自我改进（RSI）可能实现的时间从 2028 年提前到最早 2027 年。

`The Decoder：AI News（RSS）`


---

**5. [多伦多大学与Google论文：AI助手选择或成最后重大决定](https://x.com/rohanpaul_ai/status/2114251676144021818)**

> 　多伦多大学与Google的论文提出，选择AI助手可能是人们做的最后一个重大决定，此后决策都由该助手代劳。论文还指出，评估网站如何"操纵"AI回答的GEO基准需统一编辑规则，否则分数无法比较；作者按改动位置、方式和目标线索（如权威性）为每种GEO编辑打标签，并映射了11种已发表的GEO方法，但论文未做实验。

`X：Rohan Paul (@rohanpaul_ai)`


---

**6. [南京大学等团队开源 OpenMobile-2 手机智能体，27B 版 AndroidWorld 得分 79.9](https://the-decoder.com/openmobile-2-proves-open-source-smartphone-agents-can-rival-proprietary-models/)**

> 　南京大学、商汤等机构发布开源手机智能体 OpenMobile-2，基于 Qwen3.5 9B 和 Qwen3.6 27B，并公开完整训练环境、数据和复现说明。

`The Decoder：AI News（RSS）`


---

**7. [Google DeepMind 论文：主动式 AI 智能体进团队，有人视其为救星，有人感到被监视](https://x.com/rohanpaul_ai/status/2114241586989334537)**

> 　Google DeepMind 论文研究主动式 AI 智能体在大公司 20 多个团队运行 5 个月的情况，并访谈 17 名用户，发现同一智能体被部分人视为救星，另一些人却因它擅自动作而感到压力。智能体把过期文档当现状、给 VP 标记 16 个 bug、提前分享草稿海报、误读讽刺；被强推的团队比自愿采用团队更不宽容其失误。作者建议经团队同意后再部署智能体、分离权限并提供易用的撤销方式。

`X：Rohan Paul (@rohanpaul_ai)`


---

**8. [Browser Use 详解 WebArena、WebVoyager、Mind2Web 等 Web Agent 基准及选型](https://browser-use.com/posts/web-agent-benchmarks)**

> 　Browser Use 发文梳理 Web agent 基准的三类形式：沙箱站点（WebArena、VisualWebArena、WorkArena、REAL）可复现、真实网页基准（Online-Mind2Web、WebVoyager、WebBench、BrowseComp 等）最接近真实但分数随站点变化漂移、离线数据集（Mind2Web）逐步对比人类操作。

`Browser Use`


---

**9. [生成式价值分类器：无需动作条件化的Q函数](https://x.com/chelseabfinn/status/2114117117813706782)**

> 　生成式价值分类器是一种新的Q函数参数化方式，不需要动作条件化。

我们认为它们或许能与大型预训练策略优雅地结合，并从更丰富的输出信号中更好地学习和泛化。

论文：https://alexanderswerdlow.github.io/gvc/

`X：Chelsea Finn（Stanford 助理教授） (@chelseabfinn)`


---

**10. [字节 Seed 提出 Recycler：通过隐藏状态回收实现无额外成本的潜在推理](https://lf3-static.bytednsdoc.com/obj/eden-cn/hyvsmeh7uhobf/recycler_arxiv%20(2).pdf)**

> 　字节 Seed 提出 Recycler 架构，把上一 token 的顶层隐藏状态经轻量适配器与当前 token 嵌入一起送入下一步，在解码开销几乎不变的情况下保留跨步连续语义。该架构覆盖预训练、SFT、继续预训练与 RL 全流程，在数学和推理任务上参数效率突出，后期引入仍可超越参数量多 2–3 倍的模型。

`字节 Seed：Research Papers（网页内嵌数据）`


---

> 📖 更多内容请访问 [ai-daily](https://miaohua1982.github.io/ai-daily/)