from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
import psutil
import time
from collections import deque

app = FastAPI(title="Metrics Dashboard")

START_TIME = time.time()
visit_timestamps = deque()
action_counter = 0

def prune_stale_visits():
    limit = time.time() - 3600
    while visit_timestamps and visit_timestamps[0] < limit:
        visit_timestamps.popleft()

@app.middleware("http")
async def collect_visit_metrics(request, call_next):
    if request.url.path not in ["/favicon.ico", "/health"]:
        visit_timestamps.append(time.time())
        prune_stale_visits()
    return await call_next(request)

@app.get("/health")
def healthcheck():
    return {
        "status": "healthy",
        "uptime": int(time.time() - START_TIME)
    }

@app.post("/api/action")
def trigger_action():
    global action_counter
    action_counter += 1
    return HTMLResponse("<script>window.location.href='/';</script>")

@app.get("/metrics", response_class=PlainTextResponse)
def export_prometheus_metrics():
    prune_stale_visits()
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()

    return (
        f"# HELP system_cpu_usage_percent CPU load in percent\n"
        f"# TYPE system_cpu_usage_percent gauge\n"
        f"system_cpu_usage_percent {cpu}\n\n"
        f"# HELP system_memory_used_bytes Used RAM in bytes\n"
        f"# TYPE system_memory_used_bytes gauge\n"
        f"system_memory_used_bytes {mem.used}\n\n"
        f"# HELP system_memory_total_bytes Total RAM in bytes\n"
        f"# TYPE system_memory_total_bytes gauge\n"
        f"system_memory_total_bytes {mem.total}\n\n"
        f"# HELP app_requests_per_hour Total HTTP requests in the last hour\n"
        f"# TYPE app_requests_per_hour gauge\n"
        f"app_requests_per_hour {len(visit_timestamps)}\n\n"
        f"# HELP app_actions_total Total manual actions executed\n"
        f"# TYPE app_actions_total counter\n"
        f"app_actions_total {action_counter}\n"
    )

@app.get("/", response_class=HTMLResponse)
def render_dashboard():
    prune_stale_visits()
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    uptime_sec = int(time.time() - START_TIME)

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Panel | System Metrics</title>
        <style>
            :root {{
                --bg: #090a0f;
                --surface: #111318;
                --border: #1f242f;
                --text-main: #f1f5f9;
                --text-muted: #94a3b8;
                --accent: #2563eb;
                --accent-hover: #1d4ed8;
                --success: #10b981;
            }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: var(--bg);
                color: var(--text-main);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 24px;
            }}
            .container {{
                width: 100%;
                max-width: 640px;
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 32px;
            }}
            header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
                padding-bottom: 16px;
                border-bottom: 1px solid var(--border);
            }}
            h1 {{ font-size: 18px; font-weight: 600; letter-spacing: -0.02em; }}
            .badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                font-weight: 500;
                color: var(--success);
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.2);
                padding: 4px 10px;
                border-radius: 999px;
            }}
            .badge-dot {{
                width: 6px;
                height: 6px;
                background: var(--success);
                border-radius: 50%;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 16px;
            }}
            .card-title {{
                font-size: 12px;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 8px;
            }}
            .card-value {{
                font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                font-size: 20px;
                font-weight: 600;
            }}
            .action-panel {{
                margin-bottom: 24px;
            }}
            button {{
                width: 100%;
                background: var(--accent);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background 0.15s ease;
            }}
            button:hover {{ background: var(--accent-hover); }}
            footer {{
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: var(--text-muted);
                padding-top: 16px;
                border-top: 1px solid var(--border);
            }}
            footer a {{
                color: var(--text-muted);
                text-decoration: none;
                margin-left: 12px;
            }}
            footer a:hover {{ color: var(--text-main); }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Node Operations Dashboard</h1>
                <div class="badge">
                    <span class="badge-dot"></span>
                    ONLINE
                </div>
            </header>

            <section class="grid">
                <div class="card">
                    <div class="card-title">CPU Load</div>
                    <div class="card-value">{cpu}%</div>
                </div>
                <div class="card">
                    <div class="card-title">Memory Allocation</div>
                    <div class="card-value">{int(mem.used / 1048576)} / {int(mem.total / 1048576)} MB</div>
                </div>
                <div class="card">
                    <div class="card-title">Hourly Traffic</div>
                    <div class="card-value">{len(visit_timestamps)} req/h</div>
                </div>
                <div class="card">
                    <div class="card-title">Total Invocations</div>
                    <div class="card-value">{action_counter}</div>
                </div>
            </section>

            <section class="action-panel">
                <form action="/api/action" method="post">
                    <button type="submit">Dispatch Execution Event</button>
                </form>
            </section>

            <footer>
                <span>Uptime: {uptime_sec}s</span>
                <div>
                    <a href="/health" target="_blank">Healthcheck</a>
                    <a href="/metrics" target="_blank">Raw Metrics</a>
                </div>
            </footer>
        </div>
    </body>
    </html>
    """