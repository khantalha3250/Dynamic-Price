import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import ast

dataset = pd.read_csv("menu_pricing_dataset_flat20241211_123827.csv")

def expand_items_price(prices_str):
    try:
        prices_dict = ast.literal_eval(prices_str) 
        return pd.Series(prices_dict)
    except (ValueError, SyntaxError):
        return None

expanded_prices = dataset["items_price"].apply(expand_items_price)
dataset = pd.concat([dataset.drop(columns=["items_price"]), expanded_prices], axis=1)

dataset.dropna(inplace=True)

X = dataset[["temperature_f", "conditions", "rain_mm", "day", "time", "busyness_percentage"]]
y = dataset[expanded_prices.columns]  

X = pd.get_dummies(X, columns=["conditions", "day", "time"], drop_first=True)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

base_model = RandomForestRegressor(n_estimators=100, random_state=42)
multi_output_model = MultiOutputRegressor(base_model)
multi_output_model.fit(X_train, y_train)

joblib.dump(X_train.columns, "model_columns.pkl")  # Save column names for later use
joblib.dump(multi_output_model, "multi_output_menu_price_model.pkl")  # Save trained model
print("Model and column names saved.")

y_pred = multi_output_model.predict(X_test)

mae_per_item = {}
for idx, item in enumerate(y.columns):
    mae = mean_absolute_error(y_test.iloc[:, idx], y_pred[:, idx])
    mae_per_item[item] = mae

print("Mean Absolute Error per item:")
for item, error in mae_per_item.items():
    print(f"{item}: {error}")

new_data = pd.DataFrame({
    "temperature_f": [50],
    "conditions": ["clear"],
    "rain_mm": [0],
    "day": ["Monday"],
    "time": ["2 PM"],
    "busyness_percentage": [30]
})

new_data = pd.get_dummies(new_data, columns=["conditions", "day", "time"], drop_first=True)

joblib.dump(y.columns.tolist(), "model_target_columns.pkl")
target_columns = joblib.load("model_target_columns.pkl")

model_columns = joblib.load("model_columns.pkl")  
new_data = new_data.reindex(columns=model_columns, fill_value=0)

predicted_prices = multi_output_model.predict(new_data)
predicted_prices_df = pd.DataFrame(predicted_prices, columns=y.columns)

print("Predicted Prices for Each Menu Item:")
print(predicted_prices_df)
