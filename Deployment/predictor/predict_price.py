import pandas as pd
from pycaret.regression import load_model, predict_model

# Load the saved models
best_model_small_house = load_model('best_model_small_house')
best_model_large_house = load_model('best_model_large_house')

# Function to predict house price based on user input
def predict_house_price(features):
    # Determine which model to use based on 'm2'
    if features['m2'] <= 80:
        model = best_model_small_house
    else:
        model = best_model_large_house
    
    # Convert features to DataFrame
    input_df = pd.DataFrame([features])
    
    # Predict the price
    prediction = predict_model(model, data=input_df)
    
    return prediction['prediction_label'][0]
