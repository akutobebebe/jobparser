# Job Aggregator - Інструкції для запуску

## 🚀 Швидкий старт

### 1. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 2. Встановлення браузерів Playwright

```bash
playwright install webkit
```

**Linux (Fedora / RHEL / CentOS)** — install system dependencies first:

```bash
bash scripts/install_playwright_deps.sh
```

The script auto-detects your distro (Fedora, Ubuntu/Debian, Arch, openSUSE) and installs the required system libraries, then runs `playwright install webkit` automatically.

**Ubuntu / Debian** — alternative one-liner:

```bash
playwright install-deps && playwright install webkit
```

### 3. Налаштування конфігурації (опціонально)

Скопіюйте `.env.example` в `.env` і відредагуйте:

```bash
cp .env.example .env
```

### 4. Запуск Streamlit UI

```bash
streamlit run app.py
```

Інтерфейс буде доступний за адресою: **http://localhost:8501**

### 5. Запуск CLI парсера (опціонально)

```bash
python cli.py
```

---

## 📚 Детальні інструкції

### Запуск UI

**Streamlit** є основним інтерфейсом проекту:

```bash
streamlit run app.py
```

**Можливості:**
- 📊 Переглядання статистики по вакансіям
- 📋 Фільтрація та пошук вакансій
- 🔄 Запуск парсерів вручну
- ⚙️ Управління налаштуваннями

### Запуск парсера з командного рядка

```bash
python cli.py
```

Це:
1. Ініціалізує базу даних
2. Запускає всі включені парсери (Djinni, DOU)
3. Зберігає результати в БД
4. Виводить статистику

### Запуск FastAPI REST API (опціонально)

```bash
uvicorn main:app --reload
```

**Endpoints:**
- `GET /` - Root info
- `GET /jobs/` - List all jobs (з фільтрацією)
- `GET /jobs/{id}` - Job details
- `GET /stats/` - Statistics
- `POST /jobs/` - Create job
- `GET /docs` - Swagger UI

---

## 🐛 Розв'язання проблем

### Помилка: "playwright не знайдено"

```bash
pip install playwright
playwright install webkit
```

### Помилка: "Host system is missing dependencies" (Linux)

```bash
bash scripts/install_playwright_deps.sh
```

### Помилка: "SQLite database is locked"

Переконайтесь, що:
- Тільки один процес має доступ до БД
- Закрийте Streamlit і спробуйте знову

### Помилка: "Connection to DOU.ua failed"

Можливо, DOU.ua блокує запити. Спробуйте:
- Використати proxy
- Збільшити timeout у `.env`

### Помилка: "ModuleNotFoundError"

Переконайтесь, що встановлені всі залежності:

```bash
pip install -r requirements.txt --upgrade
```

---

## 🔧 Налаштування (.env)

```env
# Джерело даних БД
DATABASE_URL=sqlite:///./jobs.db

# Інтервал парсингу (у годинах)
SCRAPE_INTERVAL_HOURS=6

# Режим браузера (true = без UI)
HEADLESS_BROWSER=true

# Timeout для HTTP запитів (в сек)
REQUEST_TIMEOUT_SECONDS=30

# User-Agent для запитів
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Рівень логування: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Включити парсери
ENABLE_DJINNI=true
ENABLE_DOU=true
```

---

## 📊 Структура проекту

```
jobparser/
├── app.py                # Streamlit UI
├── main.py              # FastAPI REST API
├── cli.py               # CLI для парсингу
│
├── core/
│   ├── config.py        # Налаштування
│   └── logger.py        # Логування
│
├── database/
│   ├── models.py        # SQLAlchemy моделі
│   ├── connection.py    # Підключення БД
│   └── crud.py          # DB операції
│
├── scrapers/
│   ├── base.py          # BaseScraper
│   ├── djinni_scraper.py
│   ├── dou_scraper.py
│   └── scheduler.py     # APScheduler
│
├── utils/
│   ├── filters.py       # Фільтрація вакансій
│   └── validators.py    # Валідація даних
│
├── tests/
│   └── test_validators.py
│
├── .env.example         # Шаблон конфігурації
├── .gitignore          # Git ignore
├── requirements.txt    # Залежності
└── README.md           # Документація
```

---

## 🎯 Робочий цикл

1. **Запуск UI**: `streamlit run app.py`
2. **Натисніть "🔄 Run Scraping"** в сайдбарі
3. **Вибрати джерела**: Djinni.ua, DOU.ua
4. **Переглянути результати**: Таблиці, статистика, графіки
5. **Фільтрувати вакансії**: За рівнем, джерелом

---

## 📝 Логування

Логи зберігаються в папці `logs/`:
- `scrapers_*.log` - Логи парсерів
- `database_crud.log` - Логи БД операцій
- `core_logger.log` - Загальні логи

---

## ✅ Що готово?

- ✅ Структура проекту
- ✅ Моделі БД (SQLAlchemy)
- ✅ Парсери (Djinni, DOU)
- ✅ Streamlit UI
- ✅ REST API (FastAPI)
- ✅ Валідація даних
- ✅ Логування
- ✅ Конфігурація

## 🚧 Що робити далі?

- [ ] Установка Playwright браузерів
- [ ] Запуск парсерів та наповнення БД
- [ ] Налаштування scheduler для автоматичного оновлення
- [ ] Додавання більше джерел (LinkedIn, Indeed тощо)
- [ ] Покращення UI (графіки, аналітика)
- [ ] Deploy на сервер

---

## 📞 Поддержка

Для питань та проблем відкрийте Issue у репозиторії.

**Happy job hunting! 💼**
