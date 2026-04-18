# Threat Analytics: прогноз угроз и аналитика ИБ

Проект для хакатона: веб-приложение для аналитики киберугроз и **прогнозирования сценариев атак** по контексту организации (регион, отрасль, инфраструктура, время и т.д.). На бэкенде — REST API с JWT, агрегаты по инцидентам в БД, каталог угроз, маппинг уязвимостей на угрозы и опциональная ML-ветка (RandomForest по истории инцидентов). На фронте — дашборды, раннее предупреждение, аудит, аналитика с отчётами и экспортом в PDF.

---

## Что умеет система

- **Прогноз** (`POST /predict` и узкие эндпоинты `/predict/time`, `/target`, `/method`, `/recommendations`) — оценка риска, окна времени, цели и метода, рекомендации из каталога.
- **Аналитика** — сводная статистика по инцидентам организации (`GET /stats`, фильтры, фасеты для UI).
- **Каталог угроз** — `GET /threats` (справочник в духе ФСТЭК / доменные таблицы).
- **Маппинг уязвимостей** — `POST /vulnerabilities/map`: сопоставление CVE-подобных записей с угрозами.
- **Организации и пользователи** — регистрация по коду организации, JWT, настройки организации (`/org/settings`).
- **Наблюдаемость** — `GET /health`, `GET /ready`, метрики Prometheus при `ENABLE_METRICS=true`.

---

## Стек

| Слой | Технологии |
|------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| БД | PostgreSQL (прод/compose) или SQLite (удобно для разработки и тестов) |
| ML | scikit-learn (опционально при достаточном объёме данных в БД) |
| Frontend | React 19, Vite, TypeScript, Ant Design, Zustand |
| Инфра | Docker Compose: API, nginx + статика фронта, Postgres, Prometheus |

Схема БД накатывается **только через Alembic**. При старте API: `alembic upgrade head` и при необходимости **сиды** (флаги `RUN_MIGRATIONS_ON_START`, `RUN_SEED_ON_START` в `.env.example`). Скрипт `scripts/init_db.py` — только наполнение данными, если миграции уже применены.

---

## Быстрый старт (всё в Docker)

Из корня репозитория:

```bash
docker compose up --build -d
```

| Сервис | URL |
|--------|-----|
| Веб-интерфейс | http://127.0.0.1:8080 (nginx проксирует `/api` на backend) |
| Swagger | http://127.0.0.1:8000/docs |
| Prometheus | http://127.0.0.1:9090 |

Контейнер `api` ждёт готовности Postgres (`WAIT_FOR_DB`), затем поднимается uvicorn; миграции и сиды выполняются в **lifespan** приложения (не дублируются в entrypoint).

Ручной прогон при необходимости:

```bash
docker compose exec api python -m alembic upgrade head
docker compose exec api python scripts/init_db.py
```

Переменные окружения и логирование: см. `.env.example` (`DATABASE_URL`, `JWT_SECRET_KEY`, `LOG_LEVEL`, `LOG_FORMAT`, `ENABLE_METRICS`, флаги миграций/сидов).

---

## Локальная разработка

### 1. Репозиторий и Python

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
```

### 2. База (Postgres в Docker)

```bash
cp .env.example .env
# В .env: DATABASE_URL с postgresql+psycopg2:// и хост localhost:5433 (как в compose для сервиса db)

chmod +x scripts/bootstrap_local.sh
./scripts/bootstrap_local.sh
```

Скрипт поднимает только Postgres, применяет `alembic upgrade head`, заливает сиды и при желании прогоняет `verify_db.py`. Дальше API поднимаете сами — при старте снова выполнится upgrade (идемпотентно) и при необходимости сиды.

### 3. Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Frontend

```bash
cd frontend-vite
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Открыть: UI http://127.0.0.1:5173, Swagger http://127.0.0.1:8000/docs, Postgres с хоста — порт **5433**.

### 5. Первый вход в UI

1. Нажать «Войти», зарегистрироваться с **кодом организации** из сидов (как в исходных данных по организациям).
2. При необходимости заполнить настройки организации.
3. Проверить разделы аналитики, аудита и прогнозов.

---

## API

- Интерактивная документация: `/docs`
- OpenAPI JSON: `/openapi.json`

---

## Тесты и CI

```bash
python -m pytest tests/ -q
```

В CI: pytest для backend, для frontend — `npm ci && npm run lint && npm run build`.

---

## Git (кратко для команды)

Стабильная ветка — `main`; прямые пуши в `main` нежелательны. Фичи — в отдельных ветках (`feat/...`, `fix/...`), слияние через PR. Коммиты — осмысленные сообщения, без мусорного закомментированного кода и отладочных `print`/`console.log` в мерже.
