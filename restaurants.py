# [1] Get lowest local price
# 1. Get name, address, open times, menu items, & prices for Village from Yelp API
# 2. Get top-rated 5 restaurants in 2 km with similar menu items
# 3. DISPLAY menu items & prices for Village + each restaurant
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pprint import pprint
import json

load_dotenv()
API_KEY = os.getenv("YELP_API_KEY")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
YELP_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def fetch_webpage(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

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
    
# 1. Get name, address, open times, menu items, & prices for Village from Yelp API
def fetch_restaurant_details(soup):
    try:
        name = soup.find("h1").text.strip()
        address = soup.find("p", class_="y-css-jbomhy").text.strip()
        rating = soup.find("span", class_="y-css-1jz061g").text.strip()
        open_close_time = soup.find("span", class_="y-css-qavbuq").text.strip()
        return {"name": name, "address": address, "rating": rating, "open_close_time": open_close_time}
    except Exception as e:
        print(f"Error extracting details: {e}")
        return None
    
# 2. Get top-rated 5 restaurants in 2 km with similar menu items
def fetch_top_restaurants(lat, lon, radius=2000, limit=5, term="Indian Food"):
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

# DISPLAY menu items & prices for Village + each restaurant
def main():
    village_url = "https://www.yelp.com/biz/village-the-soul-of-india-hicksville"
    menu_url = "https://www.yelp.com/menu/village-the-soul-of-india-hicksville"
    latitude, longitude = 40.76657652292063, -73.5235058170142

    print("\n=== Restaurant Details ===")
    soup = fetch_webpage(village_url, HEADERS)
    restaurant_details = fetch_restaurant_details(soup) if soup else {}
    pprint(restaurant_details)

    print("\n=== Village Menu ===")
    village_menu = fetch_menu(menu_url, HEADERS)
    pprint(village_menu)

    print("\n=== Top Restaurants ===")
    top_restaurants = fetch_top_restaurants(latitude, longitude)
    pprint(top_restaurants)

    print("\n=== Restaurant Menus ===")
    restaurants_menu = {}
    for restaurant in top_restaurants:
        menu = fetch_menu(restaurant["menu_url"], HEADERS)
        print(f"Menu for {restaurant['name']}:")
        pprint(menu)
        restaurants_menu[restaurant["name"]] = menu  # Add the menu with the restaurant name as the key

# Save the menus to a JSON file
    with open("restaurants_menu.json", "w") as f:
        json.dump(restaurants_menu, f, indent=4)


if __name__ == "__main__":
    main()
