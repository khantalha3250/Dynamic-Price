import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import json
from pprint import pprint



API_KEY = os.getenv("YELP_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
YELP_HEADERS = {"Authorization": f"Bearer {API_KEY}"}



def fetch_webpage(url, headers):
    """
    Fetch and parse a webpage.
    """
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None


def fetch_menu(menu_url, headers):
    """
    Scrape menu details from the Yelp menu URL.
    """
    soup = fetch_webpage(menu_url, headers)
    if not soup:
        return {"Error": "Unable to fetch menu"}
    try:
        menu_items = [item.text.strip() for item in soup.find_all("h4")]
        menu_prices = [price.text.strip() for price in soup.find_all("li", class_="menu-item-price-amount")]
        return dict(zip(menu_items, menu_prices)) if len(menu_items) == len(menu_prices) else {"Error": "Incomplete menu data"}
    except Exception as e:
        print(f"Error parsing menu from {menu_url}: {e}")
        return {"Error": "Menu parsing failed"}


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
    params = {"lat": lat, "lon": lon, "appid": os.getenv("OPENWHEATHER_API_KEY")}

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


def fetch_restaurant_details(soup):
    """
    Extract restaurant details from the Yelp page soup.
    """
    try:
        name = soup.find("h1").text.strip()
        address = soup.find("p", class_="y-css-jbomhy").text.strip()
        rating = soup.find("span", class_="y-css-1jz061g").text.strip()
        open_close_time = soup.find("span", class_="y-css-qavbuq").text.strip()
        return {"name": name, "address": address, "rating": rating, "open_close_time": open_close_time}
    except Exception as e:
        print(f"Error extracting details: {e}")
        return None


def fetch_top_restaurants(lat, lon, radius=2000, limit=6, term="Indian Food"):
    """
    Fetch top-rated restaurants within the specified radius using Yelp API.
    """
    url = "https://api.yelp.com/v3/businesses/search"
    params = {"term": term, "latitude": lat, "longitude": lon, "sort_by": "rating", "radius": radius, "limit": limit}

    try:
        response = requests.get(url, headers=YELP_HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        restaurants = []
        for business in data.get("businesses", []):
            restaurant_url = business.get("url", "N/A")
            menu_url = restaurant_url.replace("/biz/", "/menu/") if "/biz/" in restaurant_url else "N/A"
            restaurants.append({
                "name": business["name"],
                "rating": business["rating"],
                "address": ", ".join(business["location"]["display_address"]),
                "phone": business.get("phone", "N/A"),
                "menu_url": menu_url,
            })
        return restaurants
    except requests.exceptions.RequestException as e:
        print(f"Error fetching top restaurants: {e}")
        return []


def normalize_item_name(name):
    """
    Normalize menu item names for comparison.
    """
    return " ".join(name.strip().lower().split())


def consolidate_menu_prices(restaurants_menu, village_name):
    """
    Consolidate menu prices for comparison across restaurants.
    """
    consolidated_prices = {}
    village_menu = restaurants_menu.get(village_name, {})

    for restaurant_name, menu in restaurants_menu.items():
        for item, price in menu.items():
            normalized_item = normalize_item_name(item)
            try:
                price_value = float(price.replace("$", "").strip())
            except ValueError:
                continue

            if normalized_item not in consolidated_prices:
                consolidated_prices[normalized_item] = {
                    "lowestPrice": price_value,
                    "villageItemPrice": None,
                    "highestPrice": price_value,
                }
            else:
                consolidated_prices[normalized_item]["lowestPrice"] = min(
                    consolidated_prices[normalized_item]["lowestPrice"], price_value
                )
                consolidated_prices[normalized_item]["highestPrice"] = max(
                    consolidated_prices[normalized_item]["highestPrice"], price_value
                )

            if restaurant_name == village_name:
                consolidated_prices[normalized_item]["villageItemPrice"] = price_value

    return {
        item: prices
        for item, prices in consolidated_prices.items()
        if prices["villageItemPrice"] is not None
    }


def main():
    # Define variables
    village_url = "https://www.yelp.com/biz/village-the-soul-of-india-hicksville"
    menu_url = "https://www.yelp.com/menu/village-the-soul-of-india-hicksville"
    place_url = "https://www.google.com/maps/place/Village+-+The+Soul+of+India/@40.7665603,-73.5261129,17z/data=!3m1!4b1!4m6!3m5!1s0x89c281752d83843d:0x1f2a365d2207b71c!8m2!3d40.7665603!4d-73.523538!16s%2Fg%2F11thj448_5?entry=ttu&g_ep=EgoyMDI0MTIwNC4wIKXMDSoASAFQAw%3D%3D"
    latitude, longitude = 40.76657652292063, -73.5235058170142

    # Fetch restaurant details
    print("\n=== Restaurant Details ===")
    soup = fetch_webpage(village_url, HEADERS)
    restaurant_details = fetch_restaurant_details(soup) if soup else {}
    if restaurant_details:
        pprint(restaurant_details)
    else:
        print("No restaurant details available.")

    # Fetch Village menu
    print("\n=== Village Menu ===")
    village_menu = fetch_menu(menu_url, HEADERS)
    pprint(village_menu)

    # Fetch top-rated restaurants
    print("\n=== Top Restaurants ===")
    top_restaurants = fetch_top_restaurants(latitude, longitude)
    if top_restaurants:
        pprint(top_restaurants)
    else:
        print("No top restaurants found.")

    # Fetch menus for all restaurants
    print("\n=== Restaurant Menus ===")
    restaurants_menu = {}
    for restaurant in top_restaurants:
        menu = fetch_menu(restaurant["menu_url"], HEADERS)
        restaurants_menu[restaurant["name"]] = menu
        print(f"Menu for {restaurant['name']}:")
        pprint(menu)

    # Consolidate prices
    print("\n=== Consolidated Prices ===")
    consolidated_prices = consolidate_menu_prices(restaurants_menu, restaurant_details.get("name", ""))
    pprint(consolidated_prices)
    with open("consolidated_prices.json", "w") as f:
        json.dump(consolidated_prices, f, indent=4)

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
