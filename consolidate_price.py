import json
from pprint import pprint
from difflib import get_close_matches


# Synonym mapping for better normalization
SYNONYM_MAP = {
    "water bottle": "water",
    "bottle water": "water",
    "soda water": "soda",
    "soft drink": "soda",
}


def normalize_item_name(name):
    """Normalize item names to a standard form."""
    name = " ".join(name.strip().lower().split())  # Remove extra spaces and lowercase
    # Replace synonyms with standard terms
    for key, standard in SYNONYM_MAP.items():
        if key in name:
            return standard
    return name


def match_similar_item(item, consolidated_prices):
    """Find the closest matching item in consolidated prices."""
    existing_items = consolidated_prices.keys()
    matches = get_close_matches(item, existing_items, n=1, cutoff=0.8)
    return matches[0] if matches else None


def consolidate_menu_prices(restaurants_menu, village_name):
    """Consolidate menu prices across restaurants."""
    consolidated_prices = {}

    for restaurant_name, menu in restaurants_menu.items():
        for item, price in menu.items():
            normalized_item = normalize_item_name(item)
            try:
                price_value = float(price.replace("$", "").strip())
            except ValueError:
                continue

            # Check if a similar item already exists
            matched_item = match_similar_item(normalized_item, consolidated_prices)
            target_item = matched_item if matched_item else normalized_item

            if target_item not in consolidated_prices:
                consolidated_prices[target_item] = {
                    "lowestPrice": price_value,
                    "villageItemPrice": None,
                    "highestPrice": price_value,
                }
            else:
                consolidated_prices[target_item]["lowestPrice"] = min(
                    consolidated_prices[target_item]["lowestPrice"], price_value
                )
                consolidated_prices[target_item]["highestPrice"] = max(
                    consolidated_prices[target_item]["highestPrice"], price_value
                )

            # Update villageItemPrice if the item is in the village menu
            if restaurant_name == village_name:
                consolidated_prices[target_item]["villageItemPrice"] = price_value

    # Filter out items where villageItemPrice is None
    return {
        item: prices
        for item, prices in consolidated_prices.items()
        if prices["villageItemPrice"] is not None
    }


def main():
    """Load data and consolidate prices."""
    with open("restaurants_menu.json", "r") as f:
        restaurants_menu = json.load(f)

    village_name = "Village the soul of india"

    consolidated_prices = consolidate_menu_prices(restaurants_menu, village_name)
    print("\n=== Consolidated Prices ===")
    pprint(consolidated_prices)

    with open("consolidated_prices.json", "w") as f:
        json.dump(consolidated_prices, f, indent=4)


if __name__ == "__main__":
    main()
