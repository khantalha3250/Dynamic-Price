# File: get_busy_times_weather.py
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def fetch_busy_times(place_url):
    """
    Scrape popular times from Google Maps.
    """
    driver = webdriver.Chrome()
    driver.get(place_url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'g2BVhd')]")))
        day_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'g2BVhd')]")

        popular_times = {}
        for index, container in enumerate(day_containers):
            day_name = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][index]
            closed_message = container.find_elements(By.XPATH, ".//div[contains(text(), 'Closed')]")
            if closed_message:
                popular_times[day_name] = "Closed"
                continue

            hourly_data = container.find_elements(By.XPATH, ".//div[@role='img']")
            day_popular_times = {}
            for hour_div in hourly_data:
                aria_label = hour_div.get_attribute("aria-label")
                if aria_label and "busy at" in aria_label:
                    parts = aria_label.split(" busy at ")
                    percentage = parts[0].strip()
                    time = parts[1].strip().replace("\u202f", " ")
                    day_popular_times[time] = percentage

            popular_times[day_name] = day_popular_times if day_popular_times else "No Data"

        return popular_times
    except Exception as e:
        print(f"Error scraping popular times: {e}")
        return None
    finally:
        driver.quit()

def fetch_weather_data(lat, lon):
    """
    Fetch weather data from the OpenWeatherMap API.
    """
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        temp_kelvin = data["main"].get("temp", 0)
        temp_fahrenheit = (temp_kelvin - 273.15) * 9 / 5 + 32
        weather_conditions = data["weather"][0].get("description", "Unknown")
        rain = data.get("rain", {}).get("1h", 0)
        return {
            "temperature_f": round(temp_fahrenheit, 2),
            "conditions": weather_conditions,
            "rain_mm": rain,
        }
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return {"Error": "Request failed"}

def main():
    place_url = "https://www.google.com/maps/place/Village+-+The+Soul+of+India/@40.7665603,-73.5261129,17z/data=!3m1!4b1!4m6!3m5!1s0x89c281752d83843d:0x1f2a365d2207b71c!8m2!3d40.7665603!4d-73.523538!16s%2Fg%2F11thj448_5?entry=ttu&g_ep=EgoyMDI0MTIwNC4wIKXMDSoASAFQAw%3D%3D"
    latitude, longitude = 40.76657652292063, -73.5235058170142

    # Fetch busy times
    print("\n=== Busy Times ===")
    busy_times = fetch_busy_times(place_url)
    pprint(busy_times)

    # Fetch weather data
    print("\n=== Weather Data ===")
    weather = fetch_weather_data(latitude, longitude)
    pprint(weather)

if __name__ == "__main__":
    main()
