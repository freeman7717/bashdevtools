# task_02_service

Небольшой сервис из двух частей:

- **FastAPI backend** хранит записи в CSV, валидирует входные данные и отдает их по API.
- **Streamlit frontend** работает **только через API**, показывает таблицу с `id`, строит графики и позволяет добавлять/удалять записи.

## Структура проекта

```text
task_02_service/
├── backend/
│   ├── main.py
│   └── data.csv
├── frontend/
│   └── app.py
├── requirements.txt
└── README.md
```

## Что реализовано

### Backend (FastAPI)

Эндпоинты:

- `GET /records` — получить все записи
- `POST /records` — добавить новую запись
- `DELETE /records/{id}` — удалить запись по `id`

Особенности:

- загрузка данных из CSV
- автодобавление столбца `id`, если в исходном CSV его нет
- валидация входных данных через Pydantic
- сохранение изменений обратно в `backend/data.csv`
- обработка ошибок, чтобы сервис не падал
- CORS включен для удобной работы frontend/backend

### Frontend (Streamlit)

- получает данные через FastAPI
- показывает таблицу со всеми записями, включая `id`
- форма добавления записи
- удаление записи по `id`
- отображение ошибок от API
- 2 графика на Plotly:
  - потребление по времени
  - цены по времени

После `POST` и `DELETE` таблица и графики обновляются.

## Установка

Рекомендуется использовать виртуальное окружение.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск backend

Из корня проекта:

```bash
uvicorn backend.main:app --reload
```

Backend будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Запуск frontend

В отдельном терминале из корня проекта:

```bash
streamlit run frontend/app.py
```

По умолчанию frontend ожидает backend по адресу `http://localhost:8000`.

Если нужен другой адрес API, можно задать переменную окружения.

### Windows (PowerShell)

```powershell
$env:API_URL="http://127.0.0.1:8000"
streamlit run frontend/app.py
```

### Linux / macOS

```bash
API_URL=http://127.0.0.1:8000 streamlit run frontend/app.py
```

## Формат записи для POST /records

Пример JSON:

```json
{
  "timestep": "2006-09-01 08:00",
  "consumption_eur": 70000,
  "consumption_sib": 19000,
  "price_eur": 410.5,
  "price_sib": 40.2
}
```

## Примеры запросов

### Получить все записи

```bash
curl http://127.0.0.1:8000/records
```

### Добавить запись

```bash
curl -X POST http://127.0.0.1:8000/records \
  -H "Content-Type: application/json" \
  -d '{
    "timestep": "2006-09-01 08:00",
    "consumption_eur": 70000,
    "consumption_sib": 19000,
    "price_eur": 410.5,
    "price_sib": 40.2
  }'
```

### Удалить запись

```bash
curl -X DELETE http://127.0.0.1:8000/records/3
```

## Где хранятся данные

Все изменения сохраняются в файл:

```text
backend/data.csv
```

Поэтому данные не пропадают после перезапуска приложения.

## Возможные ошибки

- неверный формат даты/времени
- отрицательные значения в числовых полях
- удаление несуществующего `id`
- проблемы чтения/записи CSV
- недоступность backend для frontend

Во всех случаях сервис возвращает понятную ошибку и не падает.
