from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


st.set_page_config(page_title="Рынок электроснабжения UI", layout="wide")

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
TIMEOUT = 120


def parse_api_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"HTTP {response.status_code}: {response.text}"

    if isinstance(payload, dict):
        if "errors" in payload and isinstance(payload["errors"], list):
            parts = []
            for item in payload["errors"]:
                field = item.get("field", "request")
                message = item.get("message", "Invalid value")
                parts.append(f"- {field}: {message}")
            return "\n".join(parts)

        if "detail" in payload:
            return str(payload["detail"])

        if "message" in payload:
            return str(payload["message"])

    return f"HTTP {response.status_code}: Неизвестная ошибка API"


@st.cache_data(ttl=2)
def fetch_records() -> pd.DataFrame:
    response = requests.get(f"{API_BASE}/records", timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    if not df.empty and "timestep" in df.columns:
        df["timestep"] = pd.to_datetime(df["timestep"])
        df = df.sort_values("timestep")
    return df


st.title("Рынок электроснабжения")

try:
    health = requests.get(f"{API_BASE}/health", timeout=TIMEOUT)
    health.raise_for_status()
    st.success(f"API доступен по адресу: {API_BASE}")
except requests.RequestException as exc:
    st.error(f"Не могу подключится к API: {exc}")
    st.stop()

left, right = st.columns(2)

with left:
    st.subheader("Добавить запись")
    with st.form("add_record_form"):
        timestep = st.text_input("Время", placeholder="2006-09-01 00:00")
        consumption_eur = st.text_input("Потребление энергии в Европейской части России", placeholder="62341.0")
        consumption_sib = st.text_input("Потребление энергии в Азиатской части России", placeholder="17916.0")
        price_eur = st.text_input("Цена в Европейской части России", placeholder="275.22")
        price_sib = st.text_input("Цена в Азиатской части России", placeholder="0.0")
        submitted = st.form_submit_button("Добавить")

        if submitted:
            payload = {
                "timestep": timestep,
                "consumption_eur": consumption_eur,
                "consumption_sib": consumption_sib,
                "price_eur": price_eur,
                "price_sib": price_sib,
            }
            try:
                response = requests.post(f"{API_BASE}/records", json=payload, timeout=TIMEOUT)
                if response.status_code == 201:
                    st.success("Запись успешно добавлена")
                    fetch_records.clear()
                    st.rerun()
                else:
                    st.error(parse_api_error(response))
            except requests.RequestException as exc:
                st.error(f"Запрос на добавление записи отклонён: {exc}")

with right:
    st.subheader("Удалить запись")
    with st.form("delete_record_form"):
        record_id = st.text_input("id записи", placeholder="1")
        delete_submitted = st.form_submit_button("Удалить")

        if delete_submitted:
            try:
                response = requests.delete(f"{API_BASE}/records/{record_id}", timeout=TIMEOUT)
                if response.status_code == 200:
                    st.success("Запись успешно удалена")
                    fetch_records.clear()
                    st.rerun()
                else:
                    st.error(parse_api_error(response))
            except requests.RequestException as exc:
                st.error(f"Запрос на удаление записи отклонён: {exc}")

st.subheader("Записи")
try:
    df = fetch_records()
except requests.HTTPError as exc:
    st.error(f"API вернул ошибку: {exc}")
    st.stop()
except requests.RequestException as exc:
    st.error(f"Ошибка при извлечении данных через API: {exc}")
    st.stop()


if df is not None and not df.empty:
    st.dataframe(df, use_container_width=True)

    chart_df = df.copy()
    chart_df["timestep_str"] = chart_df["timestep"].dt.strftime("%Y-%m-%d %H:%M")
    consumption_fig = px.line(
        chart_df,
        x="timestep",
        y=["consumption_eur", "consumption_sib"],
        markers=True,
        title="Потребление электроэнергии",
        labels={
            "value": "Потребление",
            "variable": "Регион",
            "timestep": "Время",
            "consumption_eur": "Европейская часть",
            "consumption_sib": "Азиатская часть",
        },
    )

    prices_fig = px.line(
        chart_df,
        x="timestep",
        y=["price_eur", "price_sib"],
        markers=True,
        title="Цены за электроэнергию",
        labels={
            "value": "Цена",
            "variable": "Регион",
            "timestep": "Время",
            "price_eur": "Европейская часть",
            "price_sib": "Азиатская часть",
        },
    )

    chart_col_1, chart_col_2 = st.columns(2)
    with chart_col_1:
        st.plotly_chart(consumption_fig, use_container_width=True)
    with chart_col_2:
        st.plotly_chart(prices_fig, use_container_width=True)

else:
    st.info("Записи не найдены.")
