from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
import psutil
import time
from collections import deque

app = FastAPI(title="DevOps Homework App")

# Время старта приложения
START_TIME = time.time()

# Очередь для хранения меток времени каждого визита
# Нужна для подсчета «посещений в час»
visit_timestamps = deque()

# Счетчик кликов по кнопке
click_counter = 0

def clean_old_visits():
    """Удаляет метки посещений старше 1 часа (3600 секунд)"""
    current_time = time.time()
    one_hour_ago = current_time - 3600
    while visit_timestamps and visit_timestamps[0] < one_hour_ago:
        visit_timestamps.popleft()

@app.middleware("http")
async def track_visits(request, call_next):
    """Этот посредник срабатывает на каждый входящий запрос"""
    # Не считаем за визит запрос favicon и системный healthcheck
    if request.url.path not in ["/favicon.ico", "/health"]:
        visit_timestamps.append(time.time())
        clean_old_visits()
    response = await call_next(request)
    return response

# 1. ТРЕБОВАНИЕ: Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "uptime_seconds": int(time.time() - START_TIME)
    }

# 2. ТРЕБОВАНИЕ: Интерфейс с кнопкой, который можно потыкать
@app.get("/", response_class=HTMLResponse)
def index_page():
    clean_old_visits()
    visits_last_hour = len(visit_timestamps)

    # Замеряем системные ресурсы
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    mem_used_mb = int(memory.used / (1024 * 1024))
    mem_total_mb = int(memory.total / (1024 * 1024))

    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>DevOps App Dashboard</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a;
                color: #f8fafc;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 40px;
                margin: 0;
            }}
            .card {{
                background: #1e293b;
                border-radius: 12px;
                padding: 24px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                width: 100%;
                max-width: 500px;
                margin-bottom: 20px;
            }}
            h1 {{ margin-top: 0; color: #38bdf8; font-size: 24px; }}
            .metric {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #334155;
            }}
            .metric:last-child {{ border-bottom: none; }}
            .value {{ font-weight: bold; color: #4ade80; }}
            button {{
                background: #0284c7;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
                transition: background 0.2s;
            }}
            button:hover {{ background: #0369a1; }}
            a {{ color: #38bdf8; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 DevOps Homework App</h1>
            <p>Статус сервиса: <span class="value">ONLINE</span></p>
            
            <form action="/click" method="post">
                <button type="submit">Тыкни меня! (Кликов: {click_counter})</button>
            </form>
        </div>

        <div class="card">
            <h3>📊 Мониторинг (Текущие метрики)</h3>
            <div class="metric">
                <span>Загрузка CPU:</span>
                <span class="value">{cpu_percent}%</span>
            </div>
            <div class="metric">
                <span>Память (RAM занято / всего):</span>
                <span class="value">{mem_used_mb} МБ / {mem_total_mb} МБ</span>
            </div>
            <div class="metric">
                <span>Посещений за последний час:</span>
                <span class="value">{visits_last_hour}</span>
            </div>
        </div>

        <div style="font-size: 14px;">
            Эндпоинты: <a href="/health" target="_blank">/health</a> | 
            <a href="/metrics" target="_blank">/metrics</a>
        </div>
    </body>
    </html>
    """

@app.post("/click")
def handle_click():
    global click_counter
    click_counter += 1
    # Возвращаемся обратно на главную страницу
    return HTMLResponse("<script>window.location.href='/';</script>")

# 3. ТРЕБОВАНИЕ: Метрики в стандартном формате Prometheus
@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    clean_old_visits()
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    
    # Формат вывода понятен стандартным системам мониторинга (Prometheus)
    return (
        f"# HELP app_cpu_usage_percent Текущий процент CPU\n"
        f"# TYPE app_cpu_usage_percent gauge\n"
        f"app_cpu_usage_percent {cpu}\n\n"
        f"# HELP app_memory_used_bytes Использовано памяти\n"
        f"# TYPE app_memory_used_bytes gauge\n"
        f"app_memory_used_bytes {mem.used}\n\n"
        f"# HELP app_memory_total_bytes Всего памяти\n"
        f"# TYPE app_memory_total_bytes gauge\n"
        f"app_memory_total_bytes {mem.total}\n\n"
        f"# HELP app_visits_last_hour_total Посещений за последний час\n"
        f"# TYPE app_visits_last_hour_total gauge\n"
        f"app_visits_last_hour_total {len(visit_timestamps)}\n\n"
        f"# HELP app_button_clicks_total Всего кликов по кнопке\n"
        f"# TYPE app_button_clicks_total counter\n"
        f"app_button_clicks_total {click_counter}\n"
    )