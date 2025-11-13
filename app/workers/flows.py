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
