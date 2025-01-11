import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE_API_URL = "http://api.openweathermap.org/data/2.5/"

month_to_season = {
    12: "winter", 
    1: "winter", 
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "autumn", 
    10: "autumn",
    11: "autumn",
}


def fetch_current_temperature(city, api_key):
    url = f"{BASE_API_URL}weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        return data["main"]["temp"]
    else:
        st.error("Ошибка при получении данных. Проверьте API-ключ.")
        return None


def process_data(data, city):
    city_data = data[data["city"] == city].copy()
    city_data["rolling_mean"] = city_data["temperature"].rolling(window=30, min_periods=1).mean()
    city_data["std_dev"] = city_data["temperature"].rolling(window=30, min_periods=1).std()
    city_data["anomaly"] = (
        (city_data["temperature"] < city_data["rolling_mean"] - 2 * city_data["std_dev"]) |
        (city_data["temperature"] > city_data["rolling_mean"] + 2 * city_data["std_dev"])
    )
    return city_data


def plot_temperature(city_data):
    fig, ax = plt.subplots()
    ax.plot(city_data["timestamp"], city_data["temperature"], label="Температура", linewidth=0.5)
    ax.fill_between(
        city_data["timestamp"],
        city_data["rolling_mean"] - 2 * city_data["std_dev"],
        city_data["rolling_mean"] + 2 * city_data["std_dev"],
        color="gray",
        alpha=0.2,
        label="Норма",
    )
    ax.scatter(
        city_data[city_data["anomaly"]]["timestamp"],
        city_data[city_data["anomaly"]]["temperature"],
        color="red",
        label="Аномалии",
    )
    ax.set_xlabel("Дата")
    ax.set_ylabel("Температура (°C)")
    ax.legend()
    ax.set_xlim(city_data["timestamp"].min(), city_data["timestamp"].max())
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate(rotation=45)
    ax.tick_params(axis='x', labelsize=8)
    st.pyplot(fig)


st.title("ДЗ 1: Анализ температурных данных и мониторинг текущей температуры")
api_key = st.text_input("Введите API-ключ OpenWeatherMap")

if api_key:
    test_url = f"{BASE_API_URL}weather?q=London&appid={api_key}&units=metric"
    test_response = requests.get(test_url)

    if test_response.status_code == 200:
        st.success("API-ключ введен корректно!")

        uploaded_file = st.file_uploader("Загрузите файл с историческими данными", type="csv")

        if uploaded_file is not None:
            data = pd.read_csv(uploaded_file)
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data = data.sort_values(by=["city", "timestamp"])

            city = st.selectbox("Выберите город", data["city"].unique())

            current_temp = fetch_current_temperature(city, api_key)
            if current_temp is not None:
                st.subheader(f"Текущая температура в {city}: {current_temp} °C")
                current_season = month_to_season[pd.Timestamp.now().month]
                historical_data = data[(data["city"] == city) & (data["season"] == current_season)]
                mean_temp = historical_data["temperature"].mean()
                std_dev = historical_data["temperature"].std()

                if current_temp < (mean_temp - 2 * std_dev) or current_temp > (mean_temp + 2 * std_dev):
                    st.error("Текущая температура аномальна для этого сезона.")
                else:
                    st.success("Текущая температура в норме для этого сезона.")

            city_data = process_data(data, city)

            st.subheader(f"Описательная статистика для {city}")
            st.write(city_data.describe())

            st.subheader("Временной ряд температур")

            min_year = city_data['timestamp'].dt.year.min()
            max_year = city_data['timestamp'].dt.year.max()
            start_year, end_year = st.slider(
                "Выберите диапазон годов",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year)
            )

            city_data = city_data[(city_data['timestamp'].dt.year >= start_year) & (city_data['timestamp'].dt.year <= end_year)]
            plot_temperature(city_data)

            st.subheader("Сезонные профили")
            season_stats = city_data.groupby("season").agg({"temperature": ["mean", "std"]})
            st.write(season_stats)
    else:
        st.error("Некорректный API-ключ. Пожалуйста, проверьте и попробуйте снова.")
