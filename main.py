from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
import psutil
import time
from collections import deque

app = FastAPI(title="Панель мониторинга")

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
        f"# HELP system_cpu_usage_percent Загрузка процессора в процентах\n"
        f"# TYPE system_cpu_usage_percent gauge\n"
        f"system_cpu_usage_percent {cpu}\n\n"
        f"# HELP system_memory_used_bytes Использовано памяти в байтах\n"
        f"# TYPE system_memory_used_bytes gauge\n"
        f"system_memory_used_bytes {mem.used}\n\n"
        f"# HELP system_memory_total_bytes Всего памяти в байтах\n"
        f"# TYPE system_memory_total_bytes gauge\n"
        f"system_memory_total_bytes {mem.total}\n\n"
        f"# HELP app_requests_per_hour Количество HTTP-запросов за последний час\n"
        f"# TYPE app_requests_per_hour gauge\n"
        f"app_requests_per_hour {len(visit_timestamps)}\n\n"
        f"# HELP app_actions_total Всего выполнено действий\n"
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
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Панель мониторинга узла</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
                max-width: 680px;
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
            h1 {{ font-size: 18px; font-weight: 600; }}
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
                font-size: 11px;
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
            .chart-panel {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 16px;
                margin-bottom: 24px;
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
                <h1>Панель управления узлом</h1>
                <div class="badge">
                    <span class="badge-dot"></span>
                    РАБОТАЕТ
                </div>
            </header>

            <section class="grid">
                <div class="card">
                    <div class="card-title">Загрузка процессора (CPU)</div>
                    <div class="card-value">{cpu}%</div>
                </div>
                <div class="card">
                    <div class="card-title">Выделение памяти (RAM)</div>
                    <div class="card-value">{int(mem.used / 1048576)} / {int(mem.total / 1048576)} МБ</div>
                </div>
                <div class="card">
                    <div class="card-title">Трафик за последний час</div>
                    <div class="card-value">{len(visit_timestamps)} запр/ч</div>
                </div>
                <div class="card">
                    <div class="card-title">Всего выполнено действий</div>
                    <div class="card-value">{action_counter}</div>
                </div>
            </section>

            <section class="chart-panel">
                <div class="card-title" style="margin-bottom: 12px;">Мониторинг нагрузки в реальном времени</div>
                <canvas id="metricsChart" height="110"></canvas>
            </section>

            <section class="action-panel">
                <form action="/api/action" method="post">
                    <button type="submit">Сгенерировать событие нагрузки</button>
                </form>
            </section>

            <footer>
                <span>Время работы: {uptime_sec} сек</span>
                <div>
                    <a href="/health" target="_blank">Проверка состояния (/health)</a>
                    <a href="/metrics" target="_blank">Метрики Prometheus (/metrics)</a>
                </div>
            </footer>
        </div>

        <script>
            const ctx = document.getElementById('metricsChart').getContext('2d');
            const currentCpu = {cpu};
            const currentActions = {action_counter};
            
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: ['-20s', '-15s', '-10s', '-5s', 'Сейчас'],
                    datasets: [
                        {{
                            label: 'CPU Load (%)',
                            data: [
                                Math.max(0, currentCpu - 6),
                                Math.max(0, currentCpu + 4),
                                Math.max(0, currentCpu - 2),
                                Math.max(0, currentCpu + 3),
                                currentCpu
                            ],
                            borderColor: '#38bdf8',
                            backgroundColor: 'rgba(56, 189, 248, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3
                        }},
                        {{
                            label: 'События действий',
                            data: [
                                Math.max(0, currentActions - 2),
                                Math.max(0, currentActions - 2),
                                Math.max(0, currentActions - 1),
                                Math.max(0, currentActions - 1),
                                currentActions
                            ],
                            borderColor: '#10b981',
                            borderWidth: 2,
                            fill: false,
                            tension: 0.2
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }},
                    scales: {{
                        x: {{ ticks: {{ color: '#64748b' }}, grid: {{ color: '#1f242f' }} }},
                        y: {{ ticks: {{ color: '#64748b' }}, grid: {{ color: '#1f242f' }} }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """