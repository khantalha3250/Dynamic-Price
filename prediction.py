import joblib
import pandas as pd

model_path = "multi_output_menu_price_model.pkl"
columns_path = "model_columns.pkl" 
targets_path = "model_target_columns.pkl"  

multi_output_model = joblib.load(model_path)
feature_columns = joblib.load(columns_path)
target_columns = joblib.load(targets_path)

print("Model, feature columns, and target columns loaded successfully.")

new_data = pd.DataFrame({
    "temperature_f": [40],
    "conditions": ["light rain"],  
    "rain_mm": [5],
    "day": ["Monday"],  
    "time": ["2 PM"],  
    "busyness_percentage": [75]
})

new_data = pd.get_dummies(new_data, columns=["conditions", "day", "time"], drop_first=False)

new_data = new_data.reindex(columns=feature_columns, fill_value=0)

if len(new_data.columns) != len(feature_columns):
    raise ValueError(f"Feature mismatch: Expected {len(feature_columns)} features, got {len(new_data.columns)}. "
                     "Check your input data and preprocessing.")

predicted_prices = multi_output_model.predict(new_data)

predicted_prices_df = pd.DataFrame(predicted_prices, columns=target_columns)

print("Predicted Prices for Each Menu Item:")
print(predicted_prices_df)
