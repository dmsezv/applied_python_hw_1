import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

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

st.title("ДЗ 1: Анализ температурных данных и мониторинг текущей температуры")
api_key = st.text_input("Введите API-ключ OpenWeatherMap")

# Проверка наличия API-ключа
if api_key:
    test_url = f"{BASE_API_URL}weather?q=London&appid={api_key}&units=metric"
    test_response = requests.get(test_url)

    if test_response.status_code == 200:
        st.success("API-ключ введен корректно!")

        # Загрузка данных
        uploaded_file = st.file_uploader("Загрузите файл с историческими данными", type="csv")

        if uploaded_file is not None:
            data = pd.read_csv(uploaded_file)
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data = data.sort_values(by=["city", "timestamp"])

            # Выбор города
            city = st.selectbox("Выберите город", data["city"].unique())

            # Фильтрация данных по выбранному городу
            city_data = data[data["city"] == city]

            # Расчет скользящего среднего и стандартного отклонения
            city_data["rolling_mean"] = city_data["temperature"].rolling(window=30, min_periods=1).mean()
            city_data["std_dev"] = city_data["temperature"].rolling(window=30, min_periods=1).std()

            # Определение аномалий
            city_data["anomaly"] = (
                city_data["temperature"]
                < (city_data["rolling_mean"] - 2 * city_data["std_dev"])
            ) | (
                city_data["temperature"]
                > (city_data["rolling_mean"] + 2 * city_data["std_dev"])
            )

            # Описательная статистика
            st.subheader(f"Описательная статистика для {city}")
            st.write(city_data.describe())

            # Визуализация временного ряда
            st.subheader("Временной ряд температур")
            fig, ax = plt.subplots()
            ax.plot(city_data["timestamp"], city_data["temperature"], label="Температура")
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
            st.pyplot(fig)

            # Получение текущей температуры
            url = f"{BASE_API_URL}weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                current_temp = response.json()["main"]["temp"]
                st.subheader(f"Текущая температура в {city}: {current_temp} °C")
                # Проверка на аномальность
                current_season = month_to_season[pd.Timestamp.now().month]
                historical_data = city_data[city_data["season"] == current_season]
                mean_temp = historical_data["temperature"].mean()
                std_dev = historical_data["temperature"].std()
                if current_temp < (mean_temp - 2 * std_dev) or current_temp > (mean_temp + 2 * std_dev):
                    st.error("Текущая температура аномальна для этого сезона.")
                else:
                    st.success("Текущая температура в норме для этого сезона.")
            else:
                st.error("Ошибка при получении данных. Проверьте API-ключ.")
    else:
        st.error("Некорректный API-ключ. Пожалуйста, проверьте и попробуйте снова.")
