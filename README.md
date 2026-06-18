# HealthChecker 🩺

Микросервис распределённого мониторинга API-эндпоинтов с алертингом в Telegram.

Следит за доступностью URL-адресов, проверяет статус-коды, время ответа и валидность SSL-сертификатов. При падении сервиса или истечении SSL — отправляет уведомление в Telegram и фиксирует инцидент в лог.

---

## Возможности

- Периодические HTTP-проверки по расписанию (интервал настраивается)
- Проверка SSL-сертификатов и времени до истечения
- Хранение истории проверок в SQLite
- Алерты в Telegram при деградации сервиса
- Структурированное логирование (консоль + ротируемые файлы)
- Полная контейнеризация через Docker

---

## Архитектура

```
┌─────────────────────────────────────────────────┐
│                  CLI (точка входа)               │
│           cli.py · Click · run / status          │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              Бизнес-логика (use cases)           │
│   checker.py · scheduler.py · alert_service.py  │
└──────────┬──────────────────────────┬───────────┘
           │                          │
┌──────────▼──────────┐  ┌────────────▼────────────┐
│     Логирование      │  │       Хранилище         │
│  logger.py · Loguru  │  │ repository.py · SQLite  │
└─────────────────────┘  └────────────┬────────────┘
                                       │
┌──────────────────────┐  ┌────────────▼────────────┐
│   Telegram-алерты    │  │   Мониторируемые URL     │
│ notifier.py · Bot API│  │ httpx · SSL · latency   │
└──────────────────────┘  └─────────────────────────┘

Конфигурация: config.py читает все параметры из .env
```

### Слои и файлы

| Файл | Слой | Ответственность |
|---|---|---|
| `cli.py` | Интерфейс | Точка входа, CLI-команды |
| `checker.py` | Бизнес-логика | HTTP-проверка одного URL |
| `scheduler.py` | Бизнес-логика | Запуск проверок по расписанию |
| `alert_service.py` | Бизнес-логика | Решение об отправке алерта |
| `notifier.py` | Инфраструктура | Отправка сообщения в Telegram |
| `repository.py` | Инфраструктура | Запись/чтение результатов из SQLite |
| `logger.py` | Инфраструктура | Настройка Loguru, ротация логов |
| `config.py` | Конфигурация | Чтение переменных окружения |

---

## Структура проекта

```
healthchecker/
├── src/
│   ├── cli.py
│   ├── checker.py
│   ├── scheduler.py
│   ├── alert_service.py
│   ├── notifier.py
│   ├── repository.py
│   ├── logger.py
│   └── config.py
├── logs/                   # создаётся автоматически
├── .env.example
├── .env                    # не коммитить!
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

| Переменная | Обязательная | Описание | Пример |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен бота из @BotFather | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | ✅ | ID чата для алертов | `-100123456789` |
| `CHECK_INTERVAL_SECONDS` | — | Интервал проверок (по умолчанию 60) | `60` |
| `REQUEST_TIMEOUT_SECONDS` | — | Таймаут HTTP-запроса (по умолчанию 10) | `10` |
| `LOG_LEVEL` | — | Уровень логов (по умолчанию INFO) | `INFO` |
| `DATABASE_PATH` | — | Путь к файлу SQLite (по умолчанию db.sqlite3) | `db.sqlite3` |
| `URLS` | ✅ | Список URL через запятую | `https://example.com,https://api.site.ru` |

---

## Запуск

### Через Docker (рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/<ВАШ_ЛОГИН>/healthchecker.git
cd healthchecker

# 2. Настроить окружение
cp .env.example .env
# отредактировать .env — добавить токен бота и URL

# 3. Запустить одной командой
docker compose up --build
```

### Локально (без Docker)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # заполнить .env

python -m src.cli run            # запустить мониторинг
python -m src.cli status         # посмотреть последние результаты
```

---

## CLI-команды

```bash
python -m src.cli run       # запустить планировщик (бесконечный цикл)
python -m src.cli status    # вывести последние N результатов из БД
python -m src.cli check     # разовая проверка всех URL прямо сейчас
```

---

## Логирование

Логи пишутся одновременно в консоль и в файл `logs/healthchecker.log` с ротацией по размеру (10 MB) и хранением за 7 дней.

```
2025-06-18 12:00:01 | INFO    | Scheduler started. Interval: 60s
2025-06-18 12:00:01 | INFO    | Checking https://example.com ...
2025-06-18 12:00:02 | INFO    | OK | 200 | 143ms | SSL valid (87 days)
2025-06-18 12:01:01 | ERROR   | FAIL | https://api.site.ru | Connection timeout
2025-06-18 12:01:01 | WARNING | Alert sent to Telegram: api.site.ru is DOWN
```

---

## Технологический стек

| Компонент | Технология |
|---|---|
| Язык | Python 3.11 |
| HTTP-клиент | httpx |
| Планировщик | APScheduler |
| CLI | Click |
| Логирование | Loguru |
| БД | SQLite + aiosqlite |
| Telegram | python-telegram-bot |
| Линтер | Flake8 + Black |
| Контейнеризация | Docker + docker-compose |

---

# Автор
#### Романовский Михаил Владимирович

Учебная практика · Модуль: Сопровождение и обслуживание ПО компьютерных систем