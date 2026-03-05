from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.csv"
CSV_LOCK = Lock()
EXPECTED_COLUMNS = [
    "id",
    "timestep",
    "consumption_eur",
    "consumption_sib",
    "price_eur",
    "price_sib",
]

app = FastAPI(title="Рынок электроснабжения API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecordCreate(BaseModel):
    timestep: str = Field(..., description="Дата в формате YYYY-MM-DD HH:MM")
    consumption_eur: float = Field(..., ge=0)
    consumption_sib: float = Field(..., ge=0)
    price_eur: float = Field(..., ge=0)
    price_sib: float = Field(..., ge=0)

    @field_validator("timestep")
    @classmethod
    def validate_timestep(cls, value: str) -> str:
        try:
            parsed = pd.to_datetime(value, format="%Y-%m-%d %H:%M", errors="raise")
        except Exception as exc:  
            raise ValueError("дата-время должно быть в формате YYYY-MM-DD HH:MM") from exc
        return parsed.strftime("%Y-%m-%d %H:%M")


class RecordResponse(RecordCreate):
    id: int


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):  
    errors: list[dict[str, str]] = []
    for err in exc.errors():
        field_path = ".".join(str(item) for item in err.get("loc", []) if item != "body")
        errors.append(
            {
                "field": field_path or "request",
                "message": err.get("msg", "Invalid value"),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": "Validation error", "errors": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": f"Internal server error: {str(exc)}"},
    )


def ensure_data_file() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"CSV файл не найден: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)
    if "id" not in df.columns:
        df.insert(0, "id", range(1, len(df) + 1))
        df.to_csv(DATA_FILE, index=False)


def load_df() -> pd.DataFrame:
    ensure_data_file()
    df = pd.read_csv(DATA_FILE)
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"В CSV файле отсутствуют необходимые колонки: {missing_columns}")
    return df[EXPECTED_COLUMNS].copy()


def save_df(df: pd.DataFrame) -> None:
    df.to_csv(DATA_FILE, index=False)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/records", response_model=list[RecordResponse])
def get_records() -> list[dict[str, Any]]:
    df = load_df()
    return df.to_dict(orient="records")


@app.post("/records", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(record: RecordCreate) -> dict[str, Any]:
    with CSV_LOCK:
        df = load_df()
        next_id = 1 if df.empty else int(df["id"].max()) + 1

        new_row = {
            "id": next_id,
            "timestep": record.timestep,
            "consumption_eur": record.consumption_eur,
            "consumption_sib": record.consumption_sib,
            "price_eur": record.price_eur,
            "price_sib": record.price_sib,
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_df(df)

    return new_row


@app.delete("/records/{record_id}")
def delete_record(record_id: int) -> dict[str, str]:
    with CSV_LOCK:
        df = load_df()

        if record_id not in df["id"].astype(int).values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Запись с id={record_id} не найдена",
            )

        df = df[df["id"].astype(int) != record_id].copy()
        save_df(df)

    return {"message": f"Запись с id={record_id} успешно удалена"}
