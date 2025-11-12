好的，请仔细搜索github , gitlab 等仓库资源，先找找有哪些 ai agent 或者 mcp 可以复用，基于你上面的分析和搜索，请先起草一个 MVP，包含你上面的几点建议。我更偏向于 python 全栈，除非 node 在某些方面有优势？

太好了，我按你偏好的 **Python 全栈** 路线，把能直接复用的开源组件都“捞出来”、标注用途，然后给出一个**可落地的 MVP 草案**（目录结构、依赖、`docker-compose`、核心流程/代码骨架、配置样例）。
（涉及站点自动化请务必遵守各站点 ToS 和隐私合规—以下仓库仅作技术参考。）

# 可复用组件清单（按模块）

* **抓取/抽取**

  * **ScrapeGraphAI**：LLM 驱动的结构化抽取管道，适合把页面转成字段（title/company/location/JD 等）。([GitHub][1])
  * **Playwright Python**：稳健的无头浏览器自动化，处理登录/分页/表单/文件上传。([GitHub][2])
  * 现成的多站点/示例抓取器（可择优借鉴、改造成自用 MCP 工具）：

    * **JobSpy**：支持 LinkedIn、Indeed、Glassdoor、ZipRecruiter、Google Jobs 等（Python 库）。([GitHub][3])
    * **Seek** 社区脚本（Selenium/Scrapy 版多份）：([GitHub][4])
    * **LinkedIn Easy Apply** 示例（自动投递样例，谨慎使用）：([GitHub][5])

* **Agent/工具编排（MCP）**

  * **MCP Python SDK**：官方 Python 实现，用来写“站点登录器/抓取器/投递器/通知器”等 MCP server。([GitHub][6])
  * **MCP servers 索引**：官方/社区 server 列表，便于参考实现风格。([GitHub][7])
  * **mcpservers.com**：第三方汇总的 MCP server 目录，快速选型或对标。([mcpservers.com][8])
  * **mcp-use**：全栈 MCP 框架（Python/TS 都可），做 demo 很省力。([GitHub][9])

* **工作流/人机回路**

  * **Temporal Python SDK**：长事务/可恢复/可重试；自带 **OpenAI Agents SDK** 的耐久集成（Public Preview），非常适合“发现岗位→等你在 Slack 点按钮→继续流程”。([GitHub][10])

* **文档解析/简历优化前处理**

  * **Unstructured**：把 PDF/DOCX/HTML 转成结构化元素，作为 LLM 提示的事实来源。([GitHub][11])

* **相似度检索/打分**

  * **pgvector + pgvector-python**：在 Postgres 里存向量并检索，少一套外部向量库。([GitHub][12])

* **通知/投递通道**

  * **Slack Python SDK**（含 Block Kit/交互按钮/Socket Mode）。([GitHub][13])
  * **Email**：先用 SMTP/SendGrid 等（示例多、易托管）。([Twilio][14])

---

# Python 全栈 MVP（第一版范围）

## 目标

* 接入 **Seek + LinkedIn（只抓取&提醒）** → Slack 人在回路确认
* 语义匹配（pgvector）+ 规则过滤
* 基于 **Unstructured** 解析上传简历；按 JD 生成**ATS 友好**的定制版（严禁捏造）
* Temporal 工作流承载“发现→确认→生成简历→草拟邮件/投递表单（预填）→确认→提交/暂缓→跟踪回执”

## 目录结构

```
jobot/
  apps/
    api/               # FastAPI：REST/Webhook
    workers/           # Temporal worker（活动/工作流）
    mcp_servers/
      seek/            # MCP server: 登录/抓取/详情
      linkedin/        # MCP server: 登录/抓取（先不自动投递）
      notifier/        # MCP server: slack/email
      resume/          # MCP server: unstructured 解析 & 导出 docx/pdf
  core/
    models/            # SQLAlchemy + Alembic
    embeddings/        # 向量化封装
    templates/         # 邮件/求职回答/封面信模板
    prompts/           # LLM 提示模板
  infra/
    docker/            # Dockerfiles
    migrations/
  configs/
    config.yaml        # 运行配置（可 env 覆盖）
  scripts/
    seed_demo_data.py
  docker-compose.yml
  pyproject.toml
  README.md
```

## 关键依赖

* `fastapi`, `uvicorn[standard]`
* `temporalio`（Python SDK）([GitHub][10])
* `playwright`（及 `playwright install`）([GitHub][2])
* `scrapegraph-ai`（抽取器，可与 Playwright 集成）([GitHub][1])
* `unstructured`（含 `unstructured[all-docs]` 选项）([GitHub][11])
* `SQLAlchemy`, `psycopg[binary]`, `alembic`
* `pgvector`, `pgvector[psycopg]`（Python 绑定）([GitHub][15])
* `slack-sdk`、`python-multipart`, `pydantic-settings`
* `mcp`（MCP Python SDK）或 `mcp-use`（快速起步）([GitHub][6])

## `docker-compose.yml`（核心服务骨架）

```yaml
version: "3.8"
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: jobot
    ports: ["5432:5432"]
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports: ["9000:9000","9001:9001"]
  temporal:
    image: temporalio/auto-setup:1.25
    environment:
      - DB=postgresql
      - POSTGRES_USER=postgres
      - POSTGRES_PWD=postgres
      - POSTGRES_SEEDS=db
    ports: ["7233:7233"]
    depends_on: [db]
  api:
    build: ./apps/api
    env_file: .env
    ports: ["8000:8000"]
    depends_on: [db, temporal]
  worker:
    build: ./apps/workers
    env_file: .env
    depends_on: [db, temporal]
```

## 配置样例（`configs/config.yaml`）

```yaml
app:
  env: dev
  tz: "Australia/Melbourne"

providers:
  llm:
    base_url: ${LLM_BASE_URL}
    api_key: ${LLM_API_KEY}
    model: "gpt-4o-mini"
  embeddings:
    model: "text-embedding-3-large"
    dim: 3072

stores:
  postgres_dsn: "postgresql+psycopg://postgres:postgres@db:5432/jobot"
  s3:
    endpoint: "http://minio:9000"
    bucket: "jobot"
    access_key: "minio"
    secret_key: "minio123"

notifiers:
  slack:
    bot_token: ${SLACK_BOT_TOKEN}
    channel: "#job-alerts"
  email:
    kind: "smtp"
    host: "smtp.gmail.com"
    port: 587
    username: ${SMTP_USER}
    password: ${SMTP_PASS}

sites:
  seek:
    enabled: true
    region: "AU"
    auth:
      # 建议走 Playwright + 账号密码/2FA；或 cookies 文件
      cookies_path: "./secrets/seek.cookies.json"
  linkedin:
    enabled: true
    easy_apply_only: true
    auth:
      cookies_path: "./secrets/linkedin.cookies.json"

rules:
  location_allow: ["Melbourne", "Sydney", "Remote-AU"]
  seniority: ["Mid", "Senior", "Staff"]
  skills_must: ["Python", "FastAPI", "Postgres"]
  min_score: 0.7

apply:
  human_in_loop: true
  rate_limit_per_site_per_hour: 15
```

## 数据表（最小集）

* `jobs(id, site, site_job_id, title, company, location, url, posted_at, jd_text, jd_embedding VECTOR(3072), meta JSONB, created_at)`
* `resumes(id, owner_email, original_file_url, parsed JSONB, base_embedding VECTOR(3072), created_at)`
* `resume_versions(id, resume_id, job_id, docx_url, pdf_url, diff_summary, created_at)`
* `applications(id, job_id, resume_version_id, status, channel, score, notes, created_at)`
* `application_events(id, application_id, event_type, payload JSONB, created_at)`

## 工作流骨架（Temporal）

* `DiscoverJobs`：按关键词/规则调用 **MCP(seek/linkedin)** → 结构化 → 向量化+规则打分 ≥ 阈值 → **Slack 通知**（按钮：查看/生成简历/忽略）。([GitHub][10])
* `TailorResume`：调用 **MCP(resume)** → 用 **Unstructured** 解析 → LLM 生成针对 JD 的版本 → 存储到 MinIO。([GitHub][11])
* `DraftSubmission`：生成邮件/表单草案；必要时 **Playwright** 预填。([GitHub][2])
* `Submit`：你在 Slack 点“发送/提交”后执行；记录回执/截图。
* `Track`：监控收件箱/站内消息更新 `applications`。

> Temporal 已发布与 OpenAI Agents SDK 的耐久集成（Public Preview），用于多轮、人机在回路的 agent 流程；虽然我们 MVP 不强依赖 Agents SDK，本项目未来可平滑接入。([Temporal][16])

## 代码片段（极简骨架）

**1) MCP Server（Seek 示例，伪码）**

```python
# apps/mcp_servers/seek/server.py
from mcp.server import Server, tool
from playwright.sync_api import sync_playwright

app = Server(name="seek")

@tool()
def search_jobs(query: str, location: str = "Melbourne"):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(storage_state="secrets/seek.cookies.json")
        page = ctx.new_page()
        page.goto("https://www.seek.com.au/")
        # ... 输入关键词/过滤条件，抓取列表与详情 ...
        # 返回结构化字段数组
        return [{"title": "...", "company": "...", "url": "...", "jd_text": "..."}]
```

（MCP Python SDK 文档/示例可参考仓库与教程）([GitHub][6])

**2) Temporal 工作流（发现→通知→等待交互）**

```python
# apps/workers/flows.py
from temporalio import workflow, activity
from integrations.slack import post_job_card, wait_for_action  # 自封装
from clients.mcp import call_tool  # 调 MCP server

@activity.defn
async def fetch_and_rank(keyword: str) -> list[dict]:
    jobs = await call_tool("seek:search_jobs", {"query": keyword})
    # 向量化 + 规则打分 ... 返回高分岗位
    return ranked_jobs

@workflow.defn
class DiscoverJobs:
    @workflow.run
    async def run(self, keyword: str):
        jobs = await workflow.execute_activity(fetch_and_rank, keyword, schedule_to_close_timeout=300)
        for j in jobs:
            action = await post_job_card(j)  # Slack 卡片带按钮
            choice = await wait_for_action(action.thread_ts)  # 等你点“生成简历/忽略”
            if choice == "TAILOR":
                await workflow.execute_child_workflow("TailorResume", j)
```

---

# 为什么优先 Python，不选 Node？

* **Playwright** 两端都很强，但我们还要接 **Temporal Python SDK**（人机回路更稳）和 **Unstructured**（成熟度/生态在 Python 明显更好），加上 `pgvector-python`、数据科学/embedding 配套都偏 Python 生态。([GitHub][10])
* 如果未来你要做 **大规模浏览器集群/前端渲染反爬对抗**，Node 在 Puppeteer/Playwright 云托管生态上也有优势，但这不是 MVP 阶段的首要矛盾。

---

# 下一步落地（我可以直接给你仓库骨架）

1. 初始化 `jobot` 仓库与上面目录/compose；跑通 **Postgres/pgvector/Temporal/MinIO** 基础设施。([GitHub][12])
2. 接通 **MCP(seek/linkedin)** 两个最小工具：`search_jobs` & `get_job_detail`；抓 5–10 条样本入库。([GitHub][7])
3. 接 **Unstructured** + 向量化；实现规则+语义混合打分；Slack 推送卡片交互。([GitHub][11])
4. `TailorResume` 工作流与导出 DOCX/PDF；生成**邮件草稿**（SMTP/SendGrid）。([GitHub][17])
5. 增加 **LinkedIn** 的“Easy Apply 人在回路”路径（仅演示/不默认自动投递）。([GitHub][5])

> 你要是点头，我就按此清单把可运行的 MVP 骨架一次性给你：poetry/uv 依赖、Alembic 迁移、一个 Seek 示例 MCP server、一个 Temporal 工作流、一个 Slack 卡片交互的最小闭环。

[1]: https://github.com/ScrapeGraphAI/Scrapegraph-ai?utm_source=chatgpt.com "GitHub - ScrapeGraphAI/Scrapegraph-ai: Python scraper based on AI"
[2]: https://github.com/microsoft/playwright-python?utm_source=chatgpt.com "GitHub - microsoft/playwright-python: Python version of the Playwright ..."
[3]: https://github.com/speedyapply/JobSpy?utm_source=chatgpt.com "Jobs scraper library for LinkedIn, Indeed, Glassdoor, Google ... - GitHub"
[4]: https://github.com/mitso2005/seekscraper?utm_source=chatgpt.com "Seek Job Scraper - GitHub"
[5]: https://github.com/nicolomantini/LinkedIn-Easy-Apply-Bot?utm_source=chatgpt.com "GitHub - nicolomantini/LinkedIn-Easy-Apply-Bot: Automate the ..."
[6]: https://github.com/modelcontextprotocol/python-sdk?utm_source=chatgpt.com "MCP Python SDK"
[7]: https://github.com/modelcontextprotocol/servers?utm_source=chatgpt.com "Model Context Protocol servers - GitHub"
[8]: https://mcpservers.com/?utm_source=chatgpt.com "MCP Servers - Model Context Protocol | The #1 MCP Server List"
[9]: https://github.com/mcp-use/mcp-use?utm_source=chatgpt.com "GitHub - mcp-use/mcp-use: mcp-use is the easiest way to interact with ..."
[10]: https://github.com/temporalio/sdk-python?utm_source=chatgpt.com "GitHub - temporalio/sdk-python: Temporal Python SDK"
[11]: https://github.com/Unstructured-IO/unstructured?utm_source=chatgpt.com "GitHub - Unstructured-IO/unstructured: Convert documents to structured ..."
[12]: https://github.com/pgvector/pgvector?utm_source=chatgpt.com "GitHub - pgvector/pgvector: Open-source vector similarity search for ..."
[13]: https://github.com/slackapi/python-slack-sdk?utm_source=chatgpt.com "GitHub - slackapi/python-slack-sdk: Slack Developer Kit for Python"
[14]: https://www.twilio.com/docs/sendgrid/for-developers/sending-email/smtp-python-code-example?utm_source=chatgpt.com "SMTP Python Code Example | SendGrid Docs | Twilio"
[15]: https://github.com/pgvector?utm_source=chatgpt.com "pgvector · GitHub"
[16]: https://temporal.io/blog/announcing-openai-agents-sdk-integration?utm_source=chatgpt.com "Production-ready agents with the OpenAI Agents SDK + Temporal"
[17]: https://github.com/sendgrid/sendgrid-python/blob/main/examples/helpers/mail_example.py?utm_source=chatgpt.com "sendgrid-python/examples/helpers/mail_example.py at main - GitHub"
