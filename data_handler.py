import pandas as pd
from datetime import datetime, time


def handle_excel(file: str) -> pd.DataFrame:
    """
    Reads the excel file and returns a dataframe
    """

    data = pd.read_excel(
        file,
        names=[
            "id",
            "creation_date",
            "system_id",
            "type",
            "status",
            "first_answer_date",
            "last_answer_date",
            "region",
        ],
        dtype={
            "id": int,
            "create_date": datetime,
            "system_id": str,
            "ticket_type": str,
            "status": str,
            "first_answer_type": str,
            "last_answer_type": datetime,
            "region": str,
        },
    )

    data.loc[data.region.isna(), "region"] = "Не указано"
    data.drop(data[data.first_answer_date == time(0, 0, 0)].index, inplace=True)
    data.drop(data[data.last_answer_date.isna()].index, inplace=True)
    data.first_answer_date = data.first_answer_date.apply(
        lambda x: x.hour * 3600 + x.minute * 60 + x.second
    )
    return data


if __name__ == "__main__":
    test_file = "data.xlsx"
    df = handle_excel(test_file)
    print(df.head())
    print(df.tail())
    print(df.shape)
