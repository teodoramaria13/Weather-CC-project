from flask import Flask
from flask import render_template
import pandas as pd
from google.cloud import storage
from io import StringIO

def get_files_from_bucket(bucket_name, path, skiprows=0, parse_dates=None):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(path)
    content = blob.download_as_text()
    return pd.read_csv(StringIO(content), skiprows=skiprows, parse_dates=parse_dates)

app = Flask(__name__)
bucket_name = "static-weather-api-proiect"
df_station = get_files_from_bucket(bucket_name, "data/stations.txt", skiprows=17)


@app.route("/")
def home():
    return render_template("home.html",
                           data=df_station[["STAID", "STANAME                                 "]].to_html())


@app.route("/api/v1/<station>/<date>")
def api(station, date):
    path = f"data/TG_STAID{station.zfill(6)}.txt"

    df = get_files_from_bucket(bucket_name, path, skiprows=20, parse_dates=["    DATE"])

    date_df = df.loc[df["    DATE"] == date]
    raw_temperature = date_df["   TG"]
    temperature = raw_temperature.squeeze() / 10

    if temperature == -999.9:
        temperature = "LOST"

    dictionary = {"station": station,
                  "date": date,
                  "temperature": temperature}

    return dictionary


@app.route("/api/v1/<station>")
def all_data(station):
    path = f"data/TG_STAID{str(station).zfill(6)}.txt"

    df = get_files_from_bucket(bucket_name, path, skiprows=20)
    df["   TG"] = df["   TG"] / 10

    result = df.to_dict(orient="records")

    for temperature in result:
        if temperature["   TG"] == -999.9:
            temperature["   TG"] = "LOST"

    return result


@app.route("/api/v1/yearly/<station>/<year>")
def on_year(station, year):
    path = f"data/TG_STAID{str(station).zfill(6)}.txt"

    df = get_files_from_bucket(bucket_name, path, skiprows=20, parse_dates=["    DATE"])

    df["   TG"] = df["   TG"] / 10

    df["    DATE"] = df["    DATE"].astype(str)
    result = df[df["    DATE"].str.startswith(year)].to_dict(orient="records")

    for temperature in result:
        if temperature["   TG"] == -999.9:
            temperature["   TG"] = "LOST"

    return result


if __name__ == "__main__":
    app.run(debug=True)