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
