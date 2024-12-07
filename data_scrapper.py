# [1] Get lowest local price
# 1. Get name, address, open times, menu items, & prices for Village from Yelp API
# 2. Get top-rated 5 restaurants in 2 km with similar menu items
# 3. DISPLAY menu items & prices for Village + each restaurant
import pandas as pd
import requests
from bs4 import BeautifulSoup
import requests

#  1. Get name, address, open times, menu items, & prices for Village from Yelp API
url = "https://www.yelp.com/biz/village-the-soul-of-india-hicksville"
menu_url="https://www.yelp.com/menu/village-the-soul-of-india-hicksville"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
menu_response = requests.get(menu_url, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")
menu_soup = BeautifulSoup(menu_response.text, "html.parser")
#name
name = soup.find("h1").text.strip()
print(name)
#address
address=soup.find("p", class_="y-css-jbomhy").text.strip()
print(address)
#rating
rating=soup.find("span", class_="y-css-1jz061g").text.strip()
print(rating)
#open and close time
open_close_time=soup.find("span", class_="y-css-qavbuq").text.strip()
print(open_close_time)
#menu items of Village
menu_items=[]
for i in menu_soup.find_all("h4"):
    menu_items.append(i.text.strip())
print(menu_items)
#Items price of Village
item_price=[]
for i in menu_soup.find_all("li", class_="menu-item-price-amount"):
    item_price.append(i.text.strip())
print(item_price)

# 2. Get top-rated 5 restaurants in 2 km with similar menu items
API_KEY = "weVH8BsT_k0yL2oEVV57e7RgG164EIDREIs7rYCFYT0ctPpn7QXHUvYw9i_SgaQmaYWPwnjzSPsyCgMoi5uNaEav4yOQrG-DXZTPs17oHAvh5nN0AVFjbrtTFgZTZ3Yx"  # Replace with your actual API key
ENDPOINT = "https://api.yelp.com/v3/businesses/search"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


params = {
    "term": "Indian Food",
    "latitude": 40.76657652292063,  # Village: The Soul of India coordinates
    "longitude": -73.5235058170142,
    "sort_by": "rating",
    "radius": 2000,  # 2 km radius
    "limit": 6  # Limit results to top 5 + 1 (Village itself)
}


response = requests.get(ENDPOINT, headers=HEADERS, params=params)
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

# Top 5 restaurants details near village (Including village there are 6 with village bieng on the top)
for idx, restaurant in enumerate(top_restaurants, start=1):
    print(f"Restaurant {idx}:")
    print(f"Name: {restaurant['name']}")
    print(f"Rating: {restaurant['rating']}")
    print(f"Address: {restaurant['address']}")
    print(f"Phone: {restaurant['phone']}")
    print(f"Menu URL: {restaurant['menu_url']}")
    print("-" * 40)

# DISPLAY menu items & prices for Village + each restaurant
restaurants_menu = {}

for restaurant in top_restaurants:
    name = restaurant["name"]
    menu_url = restaurant["menu_url"]

    try:
        response = requests.get(menu_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        menu_items = [item.text.strip() for item in soup.find_all("h4")]  # Adjust this if the tag for items is different
        menu_prices = [price.text.strip() for price in soup.find_all("li", class_="menu-item-price-amount")]

        if len(menu_items) == len(menu_prices): 
            menu_data = dict(zip(menu_items, menu_prices))
        else:
            menu_data = {menu_items[i]: menu_prices[i] if i < len(menu_prices) else "N/A" for i in range(len(menu_items))}
        restaurants_menu[name] = menu_data

    except Exception as e:
        print(f"Error fetching menu for {name}: {e}")
        restaurants_menu[name] = {"Error": "Unable to fetch menu"}

# Menu items along with prices of all the restaurant including village
for restaurant, menu in restaurants_menu.items():
    print(f"Restaurant: {restaurant}")
    for item, price in menu.items():
        print(f"  {item}: {price}")
    print("-" * 40)