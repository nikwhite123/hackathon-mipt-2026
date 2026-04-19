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

## Структура проекта

Ниже только важные части репозитория, без служебного шума и сгенерённых файлов:

```text
hackathon-mipt-2026/
├── app/                    # backend-приложение FastAPI
│   ├── api/                # HTTP-роуты и API-модули
│   ├── auth/               # JWT, зависимости авторизации, security helpers
│   ├── core/               # настройки, логирование, общие core-компоненты
│   ├── db/                 # engine/session, startup, миграционный bootstrap
│   ├── middleware/         # request-level middleware
│   ├── ml/                 # ML-логика и интеграция моделей
│   ├── models/             # SQLAlchemy-модели БД
│   ├── processors/         # вычислительные/скоринговые блоки
│   ├── repositories/       # доступ к данным и конфигам
│   ├── services/           # бизнес-логика приложения
│   ├── strategies/         # стратегии маппинга и доменные алгоритмы
│   ├── dependencies.py     # DI-сборка сервисов
│   ├── schemas.py          # Pydantic-схемы запросов/ответов
│   └── main.py             # точка входа FastAPI, маршруты и lifespan
│
├── frontend-vite/          # frontend на React + Vite
│   └── src/
│       ├── api/            # клиентские запросы к backend
│       ├── components/     # UI-компоненты
│       ├── hooks/          # react hooks
│       ├── pages/          # экранные страницы
│       ├── store/          # Zustand stores
│       ├── types/          # TS-типы
│       └── utils/          # фронтовые утилиты
│
├── cli/                    # Node.js CLI-клиент для API
│   ├── examples/           # примеры payload-файлов
│   ├── index.js            # точка входа CLI и описание команд
│   └── package.json        # зависимости и bin-конфигурация для `rt`
│
├── alembic/                # миграции БД
├── config/                 # JSON-конфиги каталога угроз, скоринга и правил
├── data/                   # исходные Excel/табличные данные
├── docker/                 # конфиги Prometheus/alerts и сопутствующая infra-конфигурация
├── models/                 # сохранённые ML-артефакты
├── notebooks/              # исследовательские и обучающие ноутбуки
├── scripts/                # утилиты для bootstrap, DB, ML train/verify
├── tests/                  # backend-тесты
├── docker-compose.yml      # локальная инфраструктура
├── requirements.txt        # Python-зависимости backend
└── README.md               # документация по проекту
```

### Кто за что отвечает

- `app/main.py` — главный backend entrypoint: поднимает FastAPI, регистрирует middleware, auth-router и основные ручки.
- `app/api/` — отдельные API-модули, которые удобно развивать независимо от `main.py`.
- `app/services/` — основная бизнес-логика. Если нужно понять, "как работает фича", чаще всего смотреть сюда.
- `app/repositories/` — слой чтения/записи данных: БД, файлы, конфиги.
- `app/models/` + `alembic/` — схема данных и её эволюция.
- `app/schemas.py` — контракт API: что принимает и что возвращает backend.
- `frontend-vite/src/pages/` — пользовательские разделы приложения.
- `frontend-vite/src/components/` — переиспользуемые элементы интерфейса.
- `cli/` — консольный клиент, который ходит в актуальные ручки backend и удобен для smoke-check / demo / ручной работы.
- `notebooks/` — EDA, baseline-модели, экспериментальные пайплайны и обучение.
- `models/` — сюда складываются сохранённые веса и ML-артефакты, которые использует backend.
- `scripts/` — operational scripts: локальный bootstrap, инициализация БД, проверка и обучение моделей.

### Куда смотреть в первую очередь

- Если нужно менять API или бизнес-логику: `app/main.py`, `app/services/`, `app/schemas.py`
- Если нужно менять данные, сиды или доступ к БД: `app/repositories/`, `app/models/`, `alembic/`, `scripts/`
- Если нужно менять UI: `frontend-vite/src/pages/`, `frontend-vite/src/components/`, `frontend-vite/src/api/`
- Если нужно менять CLI: `cli/index.js`
- Если нужно разбираться с ML/ноутбуками: `app/ml/`, `notebooks/`, `models/`

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

### 6. CLI

```bash
cd cli
npm install
npm link
rt --help
```

После `npm link` команда `rt` становится глобально доступной в системе.

Если потом нужно убрать глобальную установку:

```bash
npm unlink -g rt-threat-analytics-cli
```

CLI привязан к актуальным ручкам из `app/main.py`:

- `status` -> `GET /health`
- `ready` -> `GET /ready`
- `onboarding` -> пошаговый сценарий старта и работы с `organization_code`
- `threats` -> `GET /threats`
- `stats` -> `GET /stats`
- `stats-facets` -> `GET /stats/facets`
- `predict` -> `POST /predict`
- `predict-time` -> `POST /predict/time`
- `predict-target` -> `POST /predict/target`
- `predict-method` -> `POST /predict/method`
- `predict-recommendations` -> `POST /predict/recommendations`
- `login` -> `POST /auth/login`
- `register` -> `POST /auth/register`
- `me` -> `GET /auth/me`
- `org-lookup` -> `GET /auth/organization/by-code`
- `org-codes` -> `GET /auth/me` + `GET /stats/facets`
- `org-settings-get` -> `GET /org/settings`
- `org-settings-set` -> `POST /org/settings`
- `vuln-map` -> `POST /vulnerabilities/map`
- `openapi` -> `GET /openapi.json`

Примеры:

```bash
# Проверить backend
rt status
rt ready
rt onboarding

# Посмотреть угрозы
rt threats --limit 3

# Посмотреть openapi схему
rt openapi

# Найти организацию по известному коду
rt org-lookup 1008

# Зарегистрироваться и сохранить токен
rt register Ivan Petrov ivan@example.com Secret12345 1008
rt login ivan@example.com Secret12345
rt me
rt org-codes

# Получить/обновить настройки организации
rt org-settings-get
rt org-settings-set --region Moscow --industry telecom --host-count 1200 --technologies nginx,postgres,redis

# Получить сводку
rt stats

# Сформировать прогноз из флагов
rt predict 1008 --region Moscow --industry telecom --asset-type vpn_gateway --prefer-ml

# Сформировать прогноз из JSON payload
rt predict --payload-file ./examples/predict.sample.json

# Прогнать маппинг уязвимостей
rt vuln-map ./examples/vulnerabilities.sample.json

# Получить сырой JSON вместо форматированного вывода
rt --json openapi
```

Для переключения на другой backend используйте `--base-url` или переменную окружения `RT_API_BASE_URL`.

Если `organization_code` неизвестен заранее, самый понятный старт такой:

```bash
rt onboarding
```

Важно: в текущем `main` нет публичной ручки со списком **всех** организаций. Поэтому путь такой:

1. взять код из сидов / у команды;
2. проверить его через `rt org-lookup <code>`;
3. зарегистрироваться;
4. после логина смотреть свой контекст через `rt org-codes`.

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
