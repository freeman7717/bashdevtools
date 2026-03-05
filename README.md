Сервис для отображения/редактирования показателей потребления и цен за электроэнергию в Европейской и Азиатской части России.

Cервис из двух частей:

- **FastAPI backend** хранит записи в CSV, валидирует входные данные и отдает их по API.
- **Streamlit frontend** работает **только через API**, показывает таблицу с `id`, строит графики и позволяет добавлять/удалять записи. Отображает ошибки валидации, полученные от backend.

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

## Локальный запуск

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

## Запуск приложения на платформе Render

Для запуска сервера FastAPI осущевстляется запрос по адресу:

```text
https://electricity-api-w47m.onrender.com/health
```

Подключение к приложению Streamlit осущевстляется по адресу: 

```text
https://bashdevtools-frontend.onrender.com/
```

Если хотите запустить приложение локально, следуйте следующей инструкции:

## Запуск локального backend

Из корня проекта:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0
```

Backend будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Доступ к документации сервера:

```text
http://127.0.0.1:8000/docs
```

## Запуск локального frontend

В отдельном терминале из корня проекта:

```bash
streamlit run frontend/app.py
```

По умолчанию frontend ожидает backend по адресу `http://localhost:8000`.

Если нужен другой адрес API, можно задать переменную окружения API_BASE.

### Windows (PowerShell)

```powershell
$env:API_BASE="http://127.0.0.1:8000"
streamlit run frontend/app.py
```

### Linux / macOS

```bash
API_BASE=http://127.0.0.1:8000 streamlit run frontend/app.py
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

Все изменения сохраняются в файл:

```text
backend/data.csv
```

Поэтому данные не пропадают после перезапуска приложения.

## Возможные возвращаемые ошибки

- неверный формат даты/времени
- отрицательные значения в числовых полях
- удаление несуществующего `id`
- проблемы чтения/записи CSV
- недоступность backend для frontend
