我打算使用类似于 https://github.com/harrysun2006/awesome-llm-apps 或者 https://github.com/ScrapeGraphAI/Scrapegraph-ai 技术栈，基于 mcp 开发一个自动过滤抓取各个求职网站职位信息，并自动完善投递简历，跟踪求职申请的工具，大致要求：
1. 可以通过代码设置或者从yaml 文件中读取各种所需配置
2. 配置包括 ai model 的地址，api key，secret，以及各个求职网站，如seek.com.au, toptal.com, linkedin.com 的credentials 或者 token，还有各种工具，如发送邮件，消息通知的工具的配置信息
3. 职位匹配条件包括 地域，行业，level，技能，匹配度等等
4. 可以接受已有的doc 或者 pdf 格式的简历，提取关键信息，并根据职位信息(PD, job description) 做一定的优化，可以适当high light 职位所需技能对应的项目经验，证书等信息，基于事实做一定美化和完善
5. 需要一个后端来存储职位信息，简历，申请跟踪
6. 支持流程交互，可以通过slack或者其他更合适的工具进行，比如当发现匹配的职位时，发送信息询问是否需要申请，如果需要则进一步优化简历，并生成邮件，然后发送信息询问用户是否合适，如果合适则发送邮件或者在线提交；否则进一步优化
7. 需要对一般行业或者大企业（尤其是IT公司）使用的recruit AI 助手有足够了解，优化简历时需要能够尽可能通过公司的初步筛选，提高面试几率
如果已经有比较符合上述要求的平台请推荐，没有的话请深度思考，推荐可行的技术框架，尽可能减少开发工作量，谢谢！

这事儿可以做，而且你给的两条“路子”都能用上（MCP + AI 爬取 + 有人机协同）。下面我先给你一个“即插即用”的技术蓝图；最后附上能直接抄用的配置样例、数据表草案和核心流程。

> 先打个预防针：不少网站（尤其 LinkedIn/Seek/Toptal）在服务条款里限制自动化抓取/自动投递；实现前要确认 ToS、节流与隐私合规，并尽量优先用官方接口或邮件/RSS 方案。开源“自动投递”脚本很多，但基本都是基于浏览器自动化、且有合规风险（示例仓库仅供技术参考）。([GitHub][1])

# 总体方案（推荐选型）

**基座：Python + MCP + Playwright + Temporal + Postgres(pgvector) + FastAPI + Slack Bot**

* **抓取与结构化**：

  * 以 **ScrapeGraphAI** 为主干，做“页面➡结构化字段”的图式抓取（它就是“LLM+爬取”的组合模板）。([GitHub][2])
  * 对“复杂交互/登录/分页/表单”走 **Playwright** 无头浏览器（更稳、反爬友好一些）。
* **Agent/工具编排**：

  * 用 **MCP（Model Context Protocol）**把“求职网站登录器、抓取器、解析器、投递器、邮箱/Slack 通知器”等模块暴露成工具，便于后续扩展更多站点（MCP 官方规范与现成 server 列表可参考）。([GitHub][3])
* **简历解析与优化**：

  * **unstructured** 读取 PDF/DOCX，抽取段落、表格，再喂给 LLM；或选社区 resume-parser 作为启发/基线。([GitHub][4])
  * 根据 JD 萃取关键词并与候选项经历对齐，高亮“相符证据”（项目/证书/技能），面向 ATS 友好（少用复杂排版/图片）。
* **匹配与排序**：

  * Postgres + **pgvector** 存 embeddings，简历向量 ↔ JD 向量做相似度，叠加规则（地域/级别/薪资/签证等）。([GitHub][5])
* **流程编排**：

  * **Temporal**（或简单版用 Celery + Redis）：把“发现职位→询问是否申请→定制简历→二次确认→提交→跟踪”做成可恢复、可重试的工作流（长时间人机回合很稳）。([GitHub][6])
* **后端与存储**：

  * **FastAPI** 提供 API；Postgres 存核心数据；对象存储（MinIO/S3）放上传的简历与生成的定制版。
* **交互渠道**：

  * **Slack Bot**（或 Telegram/Email）：当发现高匹配岗位时 @你 确认，支持“继续润色/直接投递/忽略/拉黑公司”等按钮流。

---

## 你关心的 7 点如何落地

1. **配置支持 代码/文件双形态**

* 用 **Pydantic + Dynaconf/Hydra**：可从 `env`、`yaml`、`secret manager` 读取；不同环境（dev/prod）分层覆盖。

2. **多源凭据与模型参数**

* `providers.llm`配置（base_url、api_key、model 等），可接 OpenAI 兼容端点；
* `sites.seek/linkedin/toptal` 的 `credentials`/`cookies`/`2FA` 钩子；
* `notifiers`（Slack、Email）、`storages`（postgres/s3）模块化。

3. **职位匹配条件**

* 规则层：地域/行业/level/签证/薪资/合同类型…
* 语义层：JD/简历 embeddings 相似度，关键词覆盖率，负面过滤（“必须 onsite in Sydney”）。

4. **简历自动优化**

* unstructured 抽段落 → LLM 做“基于证据”的**项目要点改写/突出**；
* 生成 **ATS 友好的 DOCX/PDF**（保持标准标题、项目要点 bullet）；
* 自动插入“技能矩阵”和“JD 匹配摘要”（可选）。

5. **后端存储**（见下方表结构草案）

* `jobs`、`companies`、`resumes`、`resume_versions`、`applications`、`application_events`、`credentials`、`conversations`（人机回合日志）。

6. **流程交互（Slack 示例）**

* 机器人推送：`发现岗位：{title}@{company} 匹配度 0.82` → 按钮：[查看JD] [生成定制简历] [直接申请] [忽略]；
* 选择“生成定制简历”→ 回传预览文件 + 邮件草稿 → 你点“发送”或“继续润色”；
* 失败/验证码/附加问卷 → 机器人请求你补充或暂缓。

7. **对 ATS/企业招募 AI 的适配**

* 关键词与同义词扩写（如 “ETL”/“data pipeline”、“.NET Core”/“.NET 6”）；
* 量化成果（提升 xx%、降低 yy%、节省 zz 小时/成本）；
* 避免图片/复杂表格/页眉页脚；保持 10–12pt、标准字体；
* 附“岗位匹配摘要”（1 段话）与“技能映射表”（JD 要求 → 简历证据）。

---

## 最省力的组合（MVP 建议）

* **语言/框架**：Python 3.11、FastAPI、Pydantic
* **抓取**：Playwright + ScrapeGraphAI（结构抽取/稳固爬取二合一）([GitHub][2])
* **Agent/集成**：MCP（为 Seek/LinkedIn/Toptal/Email/Slack 各做一个 server，后续新增站点只加 server）([GitHub][3])
* **工作流**：Temporal（失败重试+人工等待节点）([GitHub][6])
* **存储**：Postgres 15 + pgvector；对象存储 MinIO；
* **文档处理**：unstructured（读 PDF/DOCX）([Unstructured][7])
* **通知**：Slack + Email（SMTP/OAuth）；
* **模型**：可插拔 OpenAI 兼容（本地或云端皆可）。

---

## 配置示例（`config.yaml`）

```yaml
app:
  env: prod
  base_url: "https://your-api.example.com"
  timezone: "Australia/Melbourne"

providers:
  llm:
    base_url: "https://your-llm-endpoint/v1"
    api_key: "${LLM_API_KEY}"
    model: "gpt-4o-mini"
    timeout_s: 60
  embeddings:
    model: "text-embedding-3-large"
    dim: 3072

storages:
  postgres:
    dsn: "postgresql+psycopg://user:pass@db:5432/jobot"
    use_pgvector: true
  s3:
    endpoint: "http://minio:9000"
    bucket: "jobot"
    access_key: "${S3_KEY}"
    secret_key: "${S3_SECRET}"

notifiers:
  slack:
    bot_token: "${SLACK_BOT_TOKEN}"
    channel: "#job-alerts"
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    username: "${SMTP_USER}"
    password: "${SMTP_PASS}"

sites:
  seek:
    enabled: true
    credentials:
      email: "you@example.com"
      password: "${SEEK_PASS}"
    region: "AU"
  linkedin:
    enabled: true
    cookies_path: "./secrets/linkedin_cookies.json"
    easy_apply_only: true
  toptal:
    enabled: false

rules:
  location_allow: ["Melbourne", "Sydney", "Remote-AU"]
  industry_allow: ["Software", "Data", "AI/ML"]
  seniority: ["Mid", "Senior", "Staff"]
  skills_must: ["Python", "FastAPI", "Postgres"]
  skills_nice: ["TypeScript", "AWS", "Kubernetes"]
  min_score: 0.70

apply:
  human_in_loop: true
  attach_cover_letter: true
  rate_limit:
    per_site_per_hour: 20
  captcha:
    provider: "manual" # or external solver id
```

---

## 数据表草案（Postgres + pgvector）

```sql
CREATE TABLE jobs (
  id BIGSERIAL PRIMARY KEY,
  site TEXT NOT NULL,
  site_job_id TEXT,
  title TEXT,
  company TEXT,
  location TEXT,
  url TEXT,
  posted_at TIMESTAMPTZ,
  jd_text TEXT,
  jd_embedding VECTOR(3072),
  meta JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE resumes (
  id BIGSERIAL PRIMARY KEY,
  owner_email TEXT,
  original_file_url TEXT,
  parsed JSONB,          -- name, contacts, skills, exp, edu...
  base_embedding VECTOR(3072),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE resume_versions (
  id BIGSERIAL PRIMARY KEY,
  resume_id BIGINT REFERENCES resumes(id),
  job_id BIGINT REFERENCES jobs(id),
  docx_url TEXT,
  pdf_url TEXT,
  diff_summary TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE applications (
  id BIGSERIAL PRIMARY KEY,
  job_id BIGINT REFERENCES jobs(id),
  resume_version_id BIGINT REFERENCES resume_versions(id),
  status TEXT,          -- drafted/submitted/interview/offer/rejected
  channel TEXT,         -- email/website/linkedin
  score REAL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE application_events (
  id BIGSERIAL PRIMARY KEY,
  application_id BIGINT REFERENCES applications(id),
  event_type TEXT,      -- found/matched/asked/approved/auto-submitted/update
  payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE credentials (
  id BIGSERIAL PRIMARY KEY,
  site TEXT,
  kind TEXT,            -- password/cookie/token
  secret JSONB,         -- 加密存储
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 工作流（Temporal 视角）

1. **DiscoverJobs**（定时/关键词订阅）
   → ScrapeGraphAI/Playwright 抓取 → 结构化字段 → 向量化 → 规则+语义打分
   → 分数≥阈值触发 **Slack 通知**（附 JD 摘要+匹配解释）
2. **HumanGate**（Slack 交互）
   → 你点“生成定制简历” or “忽略/拉黑”
3. **TailorResume**
   → unstructured 解析旧简历 → LLM 生成针对该 JD 的版本（带技能映射/量化要点）→ 产出 DOCX/PDF
4. **DraftSubmission**
   → 生成邮件/求职网站表单草案（可预填常规问答）
   → Slack 发预览按钮：“发送/继续润色/取消”
5. **Submit**
   → Email（SMTP/OAuth）或站点在线提交（Playwright），记录证据（截图/回执）
6. **Track**
   → 解析回执邮件、站点消息，更新 `applications` 与 `application_events`，若有面试/笔试邀请推送 Slack。

---

## 现成组件/参考

* **ScrapeGraphAI**：AI 驱动的爬取/抽取框架，配套编辑器 **ScrapeCraft** 可辅助设计抓取流程。([GitHub][2])
* **MCP**（协议 & servers）：把外部系统统一成“可调用工具”。([GitHub][3])
* **unstructured**（读 PDF/DOCX/HTML 等，适合做 LLM 前处理）。([Unstructured][7])
* **pgvector**（在 Postgres 里做向量检索，用它就不必额外上向量库）。([GitHub][5])
* **Temporal**（长事务/人机回合/可重试工作流）。([GitHub][6])
* **LinkedIn Easy Apply bot 等开源示例**（只作技术借鉴，注意合规）。([GitHub][1])

---

## LLM 提示模板片段（简历定制）

```text
你将收到：
- 候选人简历（结构化 JSON）
- 职位描述 JD（纯文本）

任务：
- 仅基于简历中已有事实，重写专业摘要（100-150字）与 4-6 条项目要点（每条1句，动词开头，含具体指标/规模）
- 对齐 JD 要求的技能/工具/领域名词，必要时用同义词展开
- 生成 “技能映射表”：<JD 要求> -> <简历中的证据片段>
- 输出 ATS 友好 Markdown（不含图片/表格/特殊符号），英语/中文按 JD 语言
- 严禁捏造未出现过的公司/项目/证书
```

---

## 风险与合规清单

* **ToS 与速率限制**：优先官方 API/订阅/邮件提醒；浏览器自动化需低频+人机协作；尊重 robots/隐私政策。
* **Cookie/密码安全**：加密存储，最小权限，2FA 支持；敏感日志脱敏。
* **可恢复性**：失败截图、表单草稿缓存、断点续投；Temporal/Celery 重试策略。
* **可观测性**：结构化日志、Tracing、节流仪表盘；异常/验证码报警。

---

如果你愿意，我可以按上面的方案，**先落一个 MVP**：

* 接 Seek/LinkedIn 两站（只抓取 + Slack 通知 + 人在回路的投递）；
* 用 unstructured 解析简历，自动出“针对 JD 的定制版”；
* Postgres + pgvector 建好匹配与跟踪；
* MCP 封装站点与通知工具，后续再逐步加 Toptal/邮件自动投递/问卷自动填充。

你更偏向 **Python 全栈**（FastAPI+Temporal）还是 **Node 混合**（NestJS+BullMQ，Agent 层仍用 MCP & Python 工具）？我可以直接给你起步仓库的目录骨架与首批代码片段。

[1]: https://github.com/nicolomantini/LinkedIn-Easy-Apply-Bot?utm_source=chatgpt.com "GitHub - nicolomantini/LinkedIn-Easy-Apply-Bot: Automate the ..."
[2]: https://github.com/ScrapeGraphAI/Scrapegraph-ai?utm_source=chatgpt.com "GitHub - ScrapeGraphAI/Scrapegraph-ai: Python scraper based on AI"
[3]: https://github.com/modelcontextprotocol/modelcontextprotocol?utm_source=chatgpt.com "GitHub - modelcontextprotocol/modelcontextprotocol: Specification and ..."
[4]: https://github.com/Unstructured-IO/unstructured?utm_source=chatgpt.com "GitHub - Unstructured-IO/unstructured: Convert documents to structured ..."
[5]: https://github.com/pgvector/pgvector?utm_source=chatgpt.com "GitHub - pgvector/pgvector: Open-source vector similarity search for ..."
[6]: https://github.com/temporalio/temporal?utm_source=chatgpt.com "GitHub - temporalio/temporal: Temporal service"
[7]: https://docs.unstructured.io/open-source/introduction/overview?utm_source=chatgpt.com "Overview - Unstructured"
