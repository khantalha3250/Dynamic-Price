import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


load_dotenv()
API_KEY = os.getenv("YELP_API_KEY")

# Base headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
YELP_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

#  function to fetch and parse a webpage
def fetch_webpage(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

# function to scrap menu details from Village Yelp menu Url
def fetch_menu(menu_url, headers):
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

   #function to scrap popular time from G map 
def fetch_busy_times(place_url):
    driver = webdriver.Chrome()  
    driver.get(place_url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'g2BVhd')]"))
        )

        day_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'g2BVhd')]")

        popular_times = {}

        for index, container in enumerate(day_containers):
            day_name = ["Sunday","Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][index]

            # Check if the day is marked as closed
            closed_message = container.find_elements(By.XPATH, ".//div[contains(text(), 'Closed')]")
            if closed_message:
                popular_times[day_name] = "Closed"
                continue

            # Extract busy data for the day
            hourly_data = container.find_elements(By.XPATH, ".//div[@role='img']")
            day_popular_times = {}
            for hour_div in hourly_data:
                aria_label = hour_div.get_attribute("aria-label")
                if aria_label and "busy at" in aria_label:
                    parts = aria_label.split(" busy at ")
                    percentage = parts[0].strip() 
                    time = parts[1].strip().replace("\u202f", " ")  
                    day_popular_times[time] = percentage

            # If no data is found for the day, mark it as "No Data"
            popular_times[day_name] = day_popular_times if day_popular_times else "No Data"

        return popular_times

    except Exception as e:
        print(f"Error scraping popular times: {e}")
        return None
    finally:
        driver.quit()


# Function to get weather data using OpenWeatherMap API
def fetch_weather_data(lat, lon):
  
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid":  os.getenv("OPENWHEATHER_API_KEY"),
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract weather details
        temp_kelvin = data["main"].get("temp", 0)
        temp_fahrenheit = (temp_kelvin - 273.15) * 9/5 + 32  #convert kelvin temperature to fahrenheit
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

# [1] Get lowest local price
# 1. Get name, address, open times, menu items, & prices for Village from Yelp API

village_url = "https://www.yelp.com/biz/village-the-soul-of-india-hicksville"
menu_url = "https://www.yelp.com/menu/village-the-soul-of-india-hicksville"

soup = fetch_webpage(village_url, HEADERS)
menu_soup = fetch_webpage(menu_url, HEADERS)

if soup:
    try:
        name = soup.find("h1").text.strip()
        address = soup.find("p", class_="y-css-jbomhy").text.strip()
        rating = soup.find("span", class_="y-css-1jz061g").text.strip()
        open_close_time = soup.find("span", class_="y-css-qavbuq").text.strip()
        print(f"Name: {name}")
        print(f"Address: {address}")
        print(f"Rating: {rating}")
        print(f"Open-Close Time: {open_close_time}")
    except Exception as e:
        print(f"Error extracting details from Village page: {e}")

if menu_soup:
    village_menu = fetch_menu(menu_url, HEADERS)
    print(f"Village Menu: {village_menu}")

# 2. Get top-rated 5 restaurants in 2 km with similar menu items
YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
params = {
    "term": "Indian Food",
    "latitude": 40.76657652292063,  # Village: The Soul of India coordinates
    "longitude": -73.5235058170142,
    "sort_by": "rating",
    "radius": 2000,  # 2 km radius
    "limit": 6  # Limit results to top 5 + 1 (Village itself)
}

try:
    response = requests.get(YELP_SEARCH_URL, headers=YELP_HEADERS, params=params)
    response.raise_for_status()
    data = response.json()

    top_restaurants = []
    for business in data.get("businesses", []):
        restaurant_url = business.get("url", "N/A")
        menu_url = restaurant_url.replace("/biz/", "/menu/") if "/biz/" in restaurant_url else "N/A"
        top_restaurants.append({
            "name": business["name"],
            "rating": business["rating"],
            "address": ", ".join(business["location"]["display_address"]),
            "phone": business.get("phone", "N/A"),
            "menu_url": menu_url
        })

    for idx, restaurant in enumerate(top_restaurants, start=1):
        print(f"Restaurant {idx}:")
        print(f"Name: {restaurant['name']}")
        print(f"Rating: {restaurant['rating']}")
        print(f"Address: {restaurant['address']}")
        print(f"Phone: {restaurant['phone']}")
        print(f"Menu URL: {restaurant['menu_url']}")
        print("-" * 40)

# 3. DISPLAY menu items & prices for Village + each restaurant
    restaurants_menu = {}
    for restaurant in top_restaurants:
        menu = fetch_menu(restaurant["menu_url"], HEADERS)
        restaurants_menu[restaurant["name"]] = menu

    for restaurant, menu in restaurants_menu.items():
        print(f"Restaurant: {restaurant}")
        for item, price in menu.items():
            print(f"  {item}: {price}")
        print("-" * 40)

except requests.exceptions.RequestException as e:
    print(f"Error fetching top restaurants: {e}")


# [2] Get busy times & bad weather
# 4. Get Village busy times from GMaps API
# 5. Get temperature & rain near Village
# 6. DISPLAY both
place_url = "https://www.google.com/maps/place/Village+-+The+Soul+of+India/@40.7665603,-73.5261129,17z/data=!4m6!3m5!1s0x89c281752d83843d:0x1f2a365d2207b71c!8m2!3d40.7665603!4d-73.523538!16s%2Fg%2F11thj448_5?entry=ttu&g_ep=EgoyMDI0MTIwNC4wIKXMDSoASAFQAw%3D%3D"  # Replace with actual URL
busy_time = fetch_busy_times(place_url)
print("Popular Times for All Days:", busy_time)


weather_data = fetch_weather_data(40.76657652292063, -73.5235058170142)
print("Weather Data:", weather_data)
