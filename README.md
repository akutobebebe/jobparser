# Job Aggregator & Analyzer MVP

Система для автоматичного збору, зберігання та візуалізації вакансій для Python-розробників з українських сайтів DOU.ua та Djinni.co.

## 🎯 Особливості

- ✅ **Автоматичний парсинг** вакансій з Djinni.ua та DOU.ua
- ✅ **Інтелектуальна фільтрація** за рівнем (Junior/Middle/Senior)
- ✅ **Прострий веб-інтерфейс** на Streamlit
- ✅ **SQLite база даних** для зберігання вакансій
- ✅ **Асинхронний парсинг** для швидкої роботи
- ✅ **Структурована логіка** з можливістю легко додавати нові парсери
- ✅ **Валідація даних** через Pydantic

## 📋 Требування

- Python 3.9+
- pip або poetry

## 🚀 Встановлення

### 1. Клонування репозиторію

```bash
git clone <repo-url>
cd jobparser
```

### 2. Створення віртуального середовища

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

### 3. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 4. Встановлення Playwright браузерів

```bash
playwright install chromium
```

### 5. Налаштування конфігурації

```bash
cp .env.example .env
# Відредагуйте .env за необхідності
```

## 📖 Використання

### Запуск Streamlit UI

```bash
streamlit run app.py
```

Інтерфейс буде доступний за адресою: `http://localhost:8501`

### Запуск CLI парсера

```bash
python cli.py
```

Це запустить парсинг всіх включених джерел та збереже результати в БД.

### Периодичне оновлення (Scheduler)

```bash
python -m apscheduler.schedulers.blocking  # Буде додано пізніше
```

## 🏗️ Архітектура проекту

```
project_root/
├── app.py                    # Streamlit UI
├── cli.py                    # CLI для запуску парсерів
│
├── core/
│   ├── config.py            # Налаштування проекту
│   └── logger.py            # Логування
│
├── database/
│   ├── models.py            # SQLAlchemy моделі (Job, Source)
│   ├── connection.py        # Підключення до БД
│   └── crud.py              # CRUD операції
│
├── scrapers/
│   ├── base.py              # Абстрактний BaseScraper
│   ├── djinni_scraper.py    # Реалізація для Djinni.co
│   └── dou_scraper.py       # Реалізація для DOU.ua
│
├── utils/
│   ├── filters.py           # Фільтрація та аналіз вакансій
│   └── validators.py        # Валідація даних
│
└── requirements.txt
```

## ⚙️ Налаштування (.env)

```env
# Database
DATABASE_URL=sqlite:///./jobs.db

# Scraping settings
SCRAPE_INTERVAL_HOURS=6
HEADLESS_BROWSER=true
REQUEST_TIMEOUT_SECONDS=30

# Features
ENABLE_DJINNI=true
ENABLE_DOU=true

# Logging
LOG_LEVEL=INFO
```

## 📊 Функціонал

### Streamlit UI (app.py)

1. **📊 Overview** - Статистика по вакансіям, розподіл за рівнем та джерелами
2. **📋 Jobs** - Таблиця всіх вакансій з фільтрацією
3. **🔗 Sources** - Управління джерелами парсингу

### Парсинг

- **Djinni Scraper** - Використовує Playwright для динамічного контенту
- **DOU Scraper** - Использует BeautifulSoup + httpx для статичного контенту

### Валідація

- Перевірка обов'язкових полів (title, company, url)
- Парсинг та валідація URL
- Автоматичне виявлення рівня за ключовими словами
- Парсинг діапазону зарплати

## 🔄 Робочий цикл

1. **Запуск парсера** → `app.py` (UI) або `cli.py`
2. **Завантаження сторінок** → Playwright/httpx
3. **Парсинг HTML** → BeautifulSoup + регулярні вирази
4. **Валідація даних** → Pydantic
5. **Збереження в БД** → SQLAlchemy + SQLite
6. **Відображення** → Streamlit таблиці та графіки

## 🛠️ Розширення

### Додавання нового парсера

1. Створіть клас, що наслідує `BaseScraper`:

```python
from scrapers.base import BaseScraper, JobSchema

class NewSiteScraper(BaseScraper):
    def __init__(self):
        super().__init__("newsite")
    
    async def scrape(self) -> List[JobSchema]:
        # Ваша логіка парсингу
        pass
    
    def get_source_url(self) -> str:
        return "https://newsite.com"
```

2. Додайте в `cli.py`:

```python
if settings.enable_newsite:
    new = await run_scraper(NewSiteScraper, 'newsite', db)
```

## 📝 Логування

Логи зберігаються у папці `logs/` з автоматичною ротацією (5MB на файл).

Рівні логування можна налаштувати через `.env`:

```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🐛 Відомі проблеми

- DOU.ua може блокувати частих скрейперів (додати proxy/delays)
- Playwright потребує встановлення браузерів (див. п.4 встановлення)

## 📚 Стек технологій

| Компонент | Технологія |
|-----------|-----------|
| Backend API | FastAPI (опціонально) |
| Frontend/UI | Streamlit |
| Database | SQLite + SQLAlchemy ORM |
| Scraping | Playwright + BeautifulSoup |
| Validation | Pydantic |
| Async | asyncio |

## 📄 Ліцензія

MIT

## 👨‍💻 Автор

Розроблено як MVP для аналізу ринку роботи для Python-розробників.

## 🤝 Внесення

Пропозиції та pull requests вітаються!

## 📞 Контакти

Для питань та пропозицій - відкрийте Issue у репозиторії.

---

**Статус проекту**: 🚧 Активна розробка

**Остання оновлення**: 2026-06-22
