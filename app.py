import pandas as pd
import numpy as np
import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime

@st.cache_data
def load_data():
    data = pd.read_csv('temperature_data.csv')
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    return data

def calculate_moving_average(data, window=30):
    data['moving_avg'] = data['temperature'].rolling(window=window).mean()
    data['moving_std'] = data['temperature'].rolling(window=window).std()
    data['anomaly'] = (data['temperature'] < (data['moving_avg'] - 2 * data['moving_std'])) | \
                      (data['temperature'] > (data['moving_avg'] + 2 * data['moving_std']))
    return data

def get_current_temperature(api_key, city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['main']['temp']
    else:
        st.error(f"Ошибка при получении данных: {response.json().get('message', 'Неизвестная ошибка')}")
        return None

def main():
    st.title("Анализ температурных данных и мониторинг текущей температуры")
    data = load_data()
    cities = data['city'].unique()
    selected_city = st.selectbox("Выберите город", cities)
    city_data = data[data['city'] == selected_city]
    city_data = calculate_moving_average(city_data)
    st.subheader("Временной ряд температур с аномалиями")
    fig, ax = plt.subplots()
    ax.plot(city_data['timestamp'], city_data['temperature'], label='Температура')
    ax.plot(city_data['timestamp'], city_data['moving_avg'], label='Скользящее среднее')
    ax.scatter(city_data[city_data['anomaly']]['timestamp'], city_data[city_data['anomaly']]['temperature'], color='red', label='Аномалии')
    ax.legend()
    st.pyplot(fig)
    st.subheader("Сезонные профили температуры")
    seasonal_avg = city_data.groupby('season')['temperature'].mean()
    seasonal_std = city_data.groupby('season')['temperature'].std()
    st.write("Средняя температура по сезонам:")
    st.write(seasonal_avg)
    st.write("Стандартное отклонение по сезонам:")
    st.write(seasonal_std)
    api_key = st.text_input("Введите ваш API ключ OpenWeatherMap")

    if api_key:
        current_temp = get_current_temperature(api_key, selected_city)
        if current_temp is not None:
            st.subheader("Текущая температура")
            st.write(f"Текущая температура в {selected_city}: {current_temp}°C")

            current_month = datetime.now().month
            season = {12: "winter", 1: "winter", 2: "winter",
                      3: "spring", 4: "spring", 5: "spring",
                      6: "summer", 7: "summer", 8: "summer",
                      9: "autumn", 10: "autumn", 11: "autumn"}[current_month]

            avg_temp = seasonal_avg[season]
            std_temp = seasonal_std[season]
            if (current_temp < (avg_temp - 2 * std_temp)) or (current_temp > (avg_temp + 2 * std_temp)):
                st.write("Текущая температура является аномальной для этого сезона.")
            else:
                st.write("Текущая температура находится в пределах нормы для этого сезона.")

if __name__ == "__main__":
    main()
