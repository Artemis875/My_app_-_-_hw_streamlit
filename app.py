import pandas as pd
import numpy as np
import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import asyncio  # Для асинхронных запросов
import aiohttp  # Для асинхронных HTTP-запросов

# Загрузка исторических данных
@st.cache_data  # Используем st.cache_data для кэширования данных
def load_data():
    data = pd.read_csv('temperature_data.csv')
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    return data

# Функция для вычисления скользящего среднего и стандартного отклонения
def calculate_moving_average(data, window=30):
    data['moving_avg'] = data['temperature'].rolling(window=window).mean()
    data['moving_std'] = data['temperature'].rolling(window=window).std()
    data['anomaly'] = (data['temperature'] < (data['moving_avg'] - 2 * data['moving_std'])) | \
                      (data['temperature'] > (data['moving_avg'] + 2 * data['moving_std']))
    return data

# Синхронная функция для получения текущей температуры через OpenWeatherMap API
def get_current_temperature(api_key, city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['main']['temp']
    else:
        st.error(f"Ошибка при получении данных: {response.json().get('message', 'Неизвестная ошибка')}")
        return None

# Асинхронная функция для получения текущей температуры через OpenWeatherMap API
async def get_current_temperature_async(api_key, city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data['main']['temp']
            else:
                st.error(f"Ошибка при получении данных: {await response.json().get('message', 'Неизвестная ошибка')}")
                return None

# Основная функция Streamlit
def main():
    st.title("Анализ температурных данных и мониторинг текущей температуры")

    # Загрузка данных
    data = load_data()

    # Выбор города
    cities = data['city'].unique()
    selected_city = st.selectbox("Выберите город", cities)

    # Фильтрация данных по выбранному городу
    city_data = data[data['city'] == selected_city]

    # Вычисление скользящего среднего и аномалий
    city_data = calculate_moving_average(city_data)

    # Отображение временного ряда с аномалиями
    st.subheader("Временной ряд температур с аномалиями")
    fig, ax = plt.subplots()
    ax.plot(city_data['timestamp'], city_data['temperature'], label='Температура')
    ax.plot(city_data['timestamp'], city_data['moving_avg'], label='Скользящее среднее')
    ax.scatter(city_data[city_data['anomaly']]['timestamp'], city_data[city_data['anomaly']]['temperature'], color='red', label='Аномалии')
    ax.legend()
    st.pyplot(fig)

    # Отображение сезонных профилей
    st.subheader("Сезонные профили температуры")
    seasonal_avg = city_data.groupby('season')['temperature'].mean()
    seasonal_std = city_data.groupby('season')['temperature'].std()
    st.write("Средняя температура по сезонам:")
    st.write(seasonal_avg)
    st.write("Стандартное отклонение по сезонам:")
    st.write(seasonal_std)

    # Ввод API ключа OpenWeatherMap
    api_key = st.text_input("Введите ваш API ключ OpenWeatherMap")

    if api_key:
        # Выбор между синхронным и асинхронным запросом
        use_async = st.checkbox("Использовать асинхронный запрос (рекомендуется для больших объемов данных)")

        if use_async:
            # Асинхронный запрос
            st.write("Используется асинхронный запрос...")
            current_temp = asyncio.run(get_current_temperature_async(api_key, selected_city))
        else:
            # Синхронный запрос
            st.write("Используется синхронный запрос...")
            current_temp = get_current_temperature(api_key, selected_city)

        if current_temp is not None:
            st.subheader("Текущая температура")
            st.write(f"Текущая температура в {selected_city}: {current_temp}°C")

            # Определение текущего сезона
            current_month = datetime.now().month
            season = {12: "winter", 1: "winter", 2: "winter",
                      3: "spring", 4: "spring", 5: "spring",
                      6: "summer", 7: "summer", 8: "summer",
                      9: "autumn", 10: "autumn", 11: "autumn"}[current_month]

            # Проверка на аномальность текущей температуры
            avg_temp = seasonal_avg[season]
            std_temp = seasonal_std[season]
            if (current_temp < (avg_temp - 2 * std_temp)) or (current_temp > (avg_temp + 2 * std_temp)):
                st.write("Текущая температура является аномальной для этого сезона.")
            else:
                st.write("Текущая температура находится в пределах нормы для этого сезона.")

if __name__ == "__main__":
    main()
