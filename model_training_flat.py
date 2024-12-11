import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib

def load_dataset(file_name):

    dataset = pd.read_csv(file_name)
    return dataset

def prepare_features_and_targets(dataset):

    X = dataset[["temperature_f", "conditions", "rain_mm", "day", "time", "busyness_percentage"]]

    y = dataset.filter(like="_price")

    X = pd.get_dummies(X, columns=["conditions", "day", "time"], drop_first=True)

    return X, y

def train_model(X, y):
 
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    base_model = RandomForestRegressor(n_estimators=100, random_state=42)
    multi_output_model = MultiOutputRegressor(base_model)
    multi_output_model.fit(X_train, y_train)

    y_pred = multi_output_model.predict(X_test)

    mae_per_item = {
        col: mean_absolute_error(y_test[col], y_pred[:, idx])
        for idx, col in enumerate(y.columns)
    }

    print("\nMean Absolute Error per item:")
    for item, error in mae_per_item.items():
        print(f"{item}: {error:.2f}")

    return multi_output_model, X.columns, y.columns

def save_model(model, feature_columns, target_columns):
    """
    Save the trained model and column names to files.

    Parameters:
    - model (MultiOutputRegressor): Trained model.
    - feature_columns (pd.Index): Feature column names.
    - target_columns (pd.Index): Target column names.
    """
    joblib.dump(model, "menu_price_model_flat.pkl")
    joblib.dump(feature_columns.tolist(), "model_columns_flat.pkl")
    joblib.dump(target_columns.tolist(), "model_target_columns_flat.pkl")

    print("Model and column names saved.")

if __name__ == "__main__":
    dataset_file = "menu_pricing_dataset20241211_123711.csv" 
    dataset = load_dataset(dataset_file)

    X, y = prepare_features_and_targets(dataset)

    trained_model, feature_columns, target_columns = train_model(X, y)

    save_model(trained_model, feature_columns, target_columns)