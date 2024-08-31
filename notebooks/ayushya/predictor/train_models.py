import pandas as pd
from pycaret.regression import *

# Load the dataset
url = '/Users/ayushyapare/Desktop/Ayushyas_Life/Work/Projects/Final_Project/Housing_Price_Prediction_Madrid/data/processed/scraped_data_cleaned_Emanuela_22Jul24.csv'
df_ad_housing = pd.read_csv(url)    

# Filter small houses
df_small_house = df_ad_housing[(df_ad_housing['m2'] > 0) &
                               (df_ad_housing['m2'] <= 80) &
                               (df_ad_housing['price'] > 0) &
                               (df_ad_housing['price'] <= 800000)]

# Filter large houses
df_large_house = df_ad_housing[(df_ad_housing['m2'] > 80) &
                               (df_ad_housing['m2'] < 180) &
                               (df_ad_housing['price'] > 800000) &
                               (df_ad_housing['price'] < 1800000)]

# Setup and train model for small houses
regression_setup_small = setup(
    data=df_small_house,
    target='price',
    session_id=9,
    polynomial_features=True,
    polynomial_degree=2,
    ignore_features=[],
    numeric_imputation='mean',
    categorical_imputation='mode',
    remove_multicollinearity=True,
    multicollinearity_threshold=0.9,
    transformation=True,
    transformation_method='yeo-johnson',
    normalize=True,
    normalize_method='zscore',
    log_data=False,
    log_experiment=False
)
best_models_small_house = compare_models(n_select=3)
best_model_small_house = stack_models(best_models_small_house, choose_better=True)
save_model(best_model_small_house, 'best_model_small_house')

# Setup and train model for large houses
regression_setup_large = setup(
    data=df_large_house,
    target='price',
    session_id=9,
    polynomial_features=True,
    polynomial_degree=2,
    ignore_features=[],
    numeric_imputation='mean',
    categorical_imputation='mode',
    remove_multicollinearity=True,
    multicollinearity_threshold=0.9,
    transformation=True,
    transformation_method='yeo-johnson',
    normalize=True,
    normalize_method='zscore',
    log_data=False,
    log_experiment=False
)
best_models_large_house = compare_models(n_select=3)
best_model_large_house = stack_models(best_models_large_house, choose_better=True)
save_model(best_model_large_house, 'best_model_large_house')
