import random
import csv
import json
from datetime import datetime

def generate_synthetic_data(consolidated_prices, num_entries=100, random_seed=None):
    if random_seed is not None:
        random.seed(random_seed) 

    weather_conditions = ["clear", "cloudy", "light rain", "moderate rain", "heavy rain", "snow"]
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    times_of_day = ["10 AM","11 AM","12 PM","1 PM","2 PM","3 PM","5 PM","6 PM","7 PM","8 PM","9 M","10 PM"]

    dataset = []

    for _ in range(num_entries):
        temperature_f = round(random.uniform(20, 90), 1) 
        conditions = random.choice(weather_conditions)
        rain_mm = round(random.uniform(0, 10), 1) if "rain" in conditions else 0.0
        day = random.choice(days_of_week)
        time = random.choice(times_of_day)
        busyness_percentage = round(random.uniform(20, 100), 1) 

        price_hike_multiplier = 1.0
        if busyness_percentage > 70:
            price_hike_multiplier += 0.1 
        if temperature_f < 45:
            price_hike_multiplier += 0.05  
        if conditions in ["moderate rain", "heavy rain", "snow"]:
            price_hike_multiplier += 0.15 
        if day in ["Saturday", "Sunday"]:
            price_hike_multiplier += 0.1 
        if time in ["12 PM", "1 PM", "7 PM", "8 PM"]:
            price_hike_multiplier += 0.1  

        items_price = {
            item: round(max(prices["lowestPrice"] * price_hike_multiplier, prices["villageItemPrice"]), 2)
            for item, prices in consolidated_prices.items()
        }

        dataset.append({
            "temperature_f": temperature_f,
            "conditions": conditions,
            "rain_mm": rain_mm,
            "day": day,
            "time": time,
            "busyness_percentage": busyness_percentage,
            "items_price": items_price  
        })

    return dataset


def save_to_csv(dataset, file_name="menu_pricing_dataset.csv"):
   
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write headers
        headers = ["temperature_f", "conditions", "rain_mm", "day", "time", "busyness_percentage", "items_price"]
        writer.writerow(headers)

        # Write rows
        for entry in dataset:
            writer.writerow([
                entry["temperature_f"],
                entry["conditions"],
                entry["rain_mm"],
                entry["day"],
                entry["time"],
                entry["busyness_percentage"],
                json.dumps(entry["items_price"]) 
            ])



if __name__ == "__main__":
    with open("consolidated_prices.json", "r") as f:
        consolidated_prices = json.load(f)


    dataset = generate_synthetic_data(consolidated_prices, num_entries=10000, random_seed=42)


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"menu_pricing_dataset_flat{timestamp}.csv"
    save_to_csv(dataset, file_name=file_name)

    print(f"Dataset has been saved to '{file_name}'.")
