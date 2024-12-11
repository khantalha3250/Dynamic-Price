import requests
from bs4 import BeautifulSoup
from django.http import JsonResponse
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def fetch_webpage(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def restaurant_details(request):
    url = "https://www.yelp.com/biz/village-the-soul-of-india-hicksville"
    soup = fetch_webpage(url, HEADERS)
    
    if not soup:
        return JsonResponse({"error": "Unable to fetch restaurant details."})

    try:
        name = soup.find("h1").text.strip()
        address = soup.find("p", class_="y-css-jbomhy").text.strip()
        open_close_time = soup.find("span", class_="y-css-qavbuq").text.strip()
        
        menu_url = "https://www.yelp.com/menu/village-the-soul-of-india-hicksville"
        menu_soup = fetch_webpage(menu_url, HEADERS)
        
        if not menu_soup:
            return JsonResponse({"error": "Unable to fetch menu details."})

        menu_items = [item.text.strip() for item in menu_soup.find_all("h4")]
        menu_prices = [price.text.strip() for price in menu_soup.find_all("li", class_="menu-item-price-amount")]
        menu = dict(zip(menu_items, menu_prices))

        data = {
            "name": name,
            "address": address,
            "open_close_time": open_close_time,
            "menu": menu,
        }
        return JsonResponse(data)
    except Exception as e:
        print(f"Error parsing details: {e}")
        return JsonResponse({"error": "Error parsing restaurant details."})
def top_restaurants(request):
    API_KEY = os.getenv("YELP_API_KEY")
    YELP_HEADERS = {"Authorization": f"Bearer {API_KEY}"}
    
    latitude, longitude = 40.76657652292063, -73.5235058170142
    url = "https://api.yelp.com/v3/businesses/search"
    params = {
        "term": "Indian Food",
        "latitude": latitude,
        "longitude": longitude,
        "radius": 2000,
        "sort_by": "rating",
        "limit": 6
    }

    try:
        response = requests.get(url, headers=YELP_HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        restaurants = []
        for business in data.get("businesses", []):
            restaurants.append({
                "name": business["name"],
                "rating": business["rating"],
                "address": ", ".join(business["location"]["display_address"]),
                "phone": business.get("phone", "N/A"),
                "menu_url": business.get("url", "N/A").replace("/biz/", "/menu/") if "/biz/" in business.get("url", "") else "N/A",
            })
        return JsonResponse({"restaurants": restaurants})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching top restaurants: {e}")
        return JsonResponse({"error": "Unable to fetch top restaurants."})
def menu_prices(request):
    top_restaurants_data = top_restaurants(request).json()
    if "error" in top_restaurants_data:
        return JsonResponse({"error": "Unable to fetch menus for restaurants."})
    
    menus = {}
    for restaurant in top_restaurants_data["restaurants"]:
        menu_url = restaurant["menu_url"]
        if menu_url == "N/A":
            menus[restaurant["name"]] = "No menu available"
            continue
        
        soup = fetch_webpage(menu_url, HEADERS)
        if not soup:
            menus[restaurant["name"]] = "Unable to fetch menu"
            continue

        try:
            menu_items = [item.text.strip() for item in soup.find_all("h4")]
            menu_prices = [price.text.strip() for price in soup.find_all("li", class_="menu-item-price-amount")]
            menus[restaurant["name"]] = dict(zip(menu_items, menu_prices))
        except Exception as e:
            menus[restaurant["name"]] = "Error parsing menu"
    
    return JsonResponse({"menus": menus})

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