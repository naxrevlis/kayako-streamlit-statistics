import streamlit as st
import pymongo
from data_handler import handle_excel
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

client = pymongo.MongoClient(**st.secrets["mongo"])
db = client["kayako_stat"]


def to_dataframe(input_data):
    df = pd.DataFrame(
        list(input_data),
        columns=[
            "_id",
            "id",
            "creation_date",
            "system_id",
            "type",
            "status",
            "first_answer_date",
            "last_answer_date",
            "region",
        ],
    )
    return df


st.set_page_config(layout="wide")


def to_datetime(date):
    return datetime(date.year, date.month, date.day)


with st.sidebar:
    st.write("Выбор периода")
    col1sidebar, col2sidebar = st.columns(2)
    with col1sidebar:
        selected_start_date = to_datetime(st.date_input("Начало"))
    with col2sidebar:
        selected_end_date = to_datetime(st.date_input("Конец"))

    region_list = ["РФ"]
    system_list = ["Все системы"]
    type_list = ["Все заявки"]
    status_list = ["Все статусы"]

    region_list += db["records"].distinct("region")
    system_list += db["records"].distinct("system_id")
    type_list += db["records"].distinct("type")
    status_list += db["records"].distinct("status")

    selected_region = st.selectbox("Регион", region_list, index=0)
    selected_system = st.selectbox("Система", system_list, index=0)
    selected_type = st.selectbox("Тип заявки", type_list, index=0)
    selected_status = st.selectbox("Статус", status_list, index=0)

    with st.expander("Upload file", expanded=False):
        uploaded_file = st.file_uploader(
            type=["xlsx", "xls"], label="Upload your Excel file"
        )
        clicked = st.button("Upload")

if clicked is True and uploaded_file is not None:
    data = handle_excel(uploaded_file)
    for index, row in data.iterrows():
        if db["records"].find_one({"id": row["id"]}) is None:
            db["records"].insert_one(row.to_dict())
        db["records"].replace_one({"id": row["id"]}, row.to_dict())


def default_view(start_date, end_date, region, system, query_type, status):
    region = {"$eq": region}
    system = {"$eq": system}
    query_type = {"$eq": query_type}
    status = {"$eq": status}
    if region["$eq"] == "РФ":
        region = {"$exists": True}
    if system["$eq"] == "Все системы":
        system = {"$exists": True}
    if query_type["$eq"] == "Все заявки":
        query_type = {"$exists": True}
    if status["$eq"] == "Все статусы":
        status = {"$exists": True}
    query = {
        "creation_date": {"$gte": start_date, "$lte": end_date + timedelta(days=1)},
        "region": region,
        "system_id": system,
        "type": query_type,
        "status": status,
    }
    res = db["records"].find(query)
    df = pd.DataFrame.from_records(res)
    df["resolution_time"] = (
        pd.to_datetime(df["last_answer_date"]) - pd.to_datetime(df["creation_date"])
    ).dt.days
    count = df.shape[0]
    st.write(f"Всего заявок в запросе: {count}")

    if count != 0:
        st.write(f"Количество заявок по типу системы")
        st.bar_chart(df["system_id"].value_counts(), height=500)
        st.write("Тип заявок")
        st.bar_chart(df["type"].value_counts(), height=300)
        st.write("Время решения заявок")
        st.write(f"Среднее время решения заявки: {df['resolution_time'].mean()}")
        st.write(f"Медианное время решения заявки: {df['resolution_time'].median()}")
        st.bar_chart(df["resolution_time"].value_counts(), height=300)

        # Pie chart, where the slices will be ordered and plotted counter-clockwise:
        requests_by_type = df["type"].value_counts()
        requests_by_status = df["status"].value_counts()

        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(
                requests_by_type,
                values="type",
                names=requests_by_type.index,
                title="Количество заявок по типу",
            )
            fig.update_traces(hoverinfo="label+percent", textinfo="value")
            st.plotly_chart(fig)
        with col2:
            fig = px.pie(
                requests_by_status,
                values="status",
                names=requests_by_status.index,
                title="Количество заявок по статусу",
            )
            fig.update_traces(hoverinfo="label+percent", textinfo="value")
            st.plotly_chart(fig)


st.write("""Kayako Statistics""")
default_view(
    selected_start_date,
    selected_end_date,
    selected_region,
    selected_system,
    selected_type,
    selected_status,
)
