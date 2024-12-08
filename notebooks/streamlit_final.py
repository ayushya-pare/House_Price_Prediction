import pandas as pd
import numpy as np
import pickle
import streamlit as st
#import lightgbm as lgb 
from sklearn.pipeline import Pipeline
from pycaret.regression import load_model, predict_model
import requests
from opencage.geocoder import OpenCageGeocode
from geopy.distance import geodesic
from neighborhoods import madrid_districts_dict


custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    body { font-family: 'Poppins', sans-serif; }
    .css-1v3fvcr { background-color: #000000; }
    .css-1emrehy { background-color: #f57c00; color: #ffffff; }
    .css-1v0mbdj { color: #f57c00; }
    .css-16huue1 { color: #ffffff; }
    .css-12tt5k5 { background-color: #000000; }
</style>
"""

# Apply the custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

#Load the saved model using pickle
model_pipeline = load_model('deployment_26072024')

st.title('Madrid House Price Prediction')

# Load the district data
district_data = pd.read_csv('prices_m2.csv')

# Load the Airbnb rent data
airbnb_data = pd.read_csv('airbnb_rent.csv')




# Hardcoded OpenCage API key
API_KEY = "46f6ec6a67a04a279a29e10a9ae7b28a"  


# Function to get coordinates using OpenCage Geocoder
def get_coordinates(address, API_KEY):
    geocoder = OpenCageGeocode(API_KEY)
    result = geocoder.geocode(address)
    if result and len(result):
        return result[0]['geometry']['lat'], result[0]['geometry']['lng']
    else:
        raise ValueError("Address not found.")

# Function to calculate the distance between two coordinates
def calculate_distance(coord1, coord2):
    return geodesic(coord1, coord2).kilometers

# Function to find the nearest tram station using OpenStreetMap Overpass API
def get_nearest_tram_station(lat, lon):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    node
      ["public_transport"="platform"]["bus"="yes"]
      (around:5000,{lat},{lon});
    out body;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    if not data['elements']:
        raise ValueError("No tram stations found within 5km radius.")

    # Find the nearest tram station
    nearest_station = None
    min_distance = float('inf')
    for element in data['elements']:
        station_coords = (element['lat'], element['lon'])
        distance = geodesic((lat, lon), station_coords).kilometers
        if distance < min_distance:
            min_distance = distance
            nearest_station = element

    return nearest_station, min_distance

def calculate_distances(street, postal_code, city):
    address = f"{street}, {postal_code}, {city}"
    
    # Predefined coordinates
    city_center = (40.416775, -3.703790)  # Puerta del Sol, Madrid
    castellana = (40.448466, -3.690612)  # Castellana, Madrid

    try:
        # Get coordinates for the given address
        lat, lon = get_coordinates(address, API_KEY)
        address_coords = (lat, lon)

        # Calculate distances
        distance_to_city_center = calculate_distance(address_coords, city_center)
        distance_to_castellana = calculate_distance(address_coords, castellana)

        # Find the nearest tram station
        _, distance_to_station = get_nearest_tram_station(lat, lon)

        return {
            "distance_city_center": distance_to_city_center,
            "distance_castellana": distance_to_castellana,
            "distance_metro": distance_to_station
        }

    except ValueError as e:
        print(f"Error for address '{address}': {e}")
        return None


# Input fields for address
#st.subheader("Address of the House:")
street = st.text_input('Street Name')


# Create two columns in Streamlit for input fields
col1, col2 = st.columns(2)

with col1:
    postal_code = st.text_input('Postal Code')
    rooms = st.number_input("Number of Rooms", step=1, format="%d", min_value=1, max_value=6)
    district = st.selectbox("District", list(madrid_districts_dict.keys()))
    with st.expander("Select Amenities"):
        has_ac = 1 if st.checkbox("AC") else 0
        elevator = 1 if st.checkbox("Elevator") else 0
        garage = 1 if st.checkbox("Garage") else 0
        has_pool = 1 if st.checkbox("Pool") else 0    
        has_terrace = 1 if st.checkbox("Terrace") else 0
        
    m2 = st.slider('Size of house in square meters', min_value=50, max_value=150)

neighbourhoods = [neighbourhood for neighbourhood in madrid_districts_dict[district]]

with col2:
    city = st.text_input('City')
    bathrooms = st.number_input("Number of Bathrooms", step=1, format="%d", min_value=1, max_value=6)
    neighbourhood = st.selectbox("Neighbourhood", neighbourhoods)
    with st.expander("Select Orientation"):
        has_orientation_east = 1 if st.checkbox("East") else 0
        has_orientation_west = 1 if st.checkbox("West") else 0
        has_orientation_north = 1 if st.checkbox("North") else 0
        has_orientation_south = 1 if st.checkbox("South") else 0
    built_year = st.slider('Built Year', min_value=1965, max_value=2023)

#address = f"{street}, {postal_code}, {city}"
#district, neighbourhood = get_district_and_neighborhood(street, postal_code, city)

# Get district-specific values
district_info = district_data[district_data['district'] == district].iloc[0]
price_m2_Q2_2024 = district_info['price_m2_Q2_2024']
cagr = district_info['CAGR']
district_affordability = district_info['district_affordability']

# Filter airbnb_data to get the airbnb_price_per_night based on the selected values
filtered_airbnb_data = airbnb_data[
    (airbnb_data['neighbourhood'] == neighbourhood) &
    #(airbnb_data['district'] == district) &
    (airbnb_data['bathrooms'] == bathrooms) &
    (airbnb_data['rooms'] == rooms)
]

# Set airbnb_price_per_night to the mean price if there are multiple entries
if not filtered_airbnb_data.empty:
    filtered_airbnb_data['price'] = filtered_airbnb_data['price'].str.strip('$').str.replace(',', '').astype(float)
    airbnb_price_per_night = filtered_airbnb_data['price'].mean()
else:
    airbnb_price_per_night = 0

if st.button('Predict House Price'):
    distances = calculate_distances(street, postal_code, city)
    if distances:
        input_data = {
            'bathrooms': bathrooms,
            'distance_castellana': distances["distance_castellana"],
            'has_pool': has_pool,
            'has_orientation_east': has_orientation_east,
            'has_orientation_north': has_orientation_north,
            'm2': m2,
            'district_affordability': district_affordability,
            'rooms': rooms,
            'distance_city_center': distances["distance_city_center"],
            'has_ac':has_ac,
            'has_orientation_west':has_orientation_west,
            'has_orientation_south':has_orientation_south,
            'built_year':built_year,
            'CAGR':cagr,
            'price_m2_Q2_2024':price_m2_Q2_2024,
            'distance_metro':distances["distance_metro"],
            'has_terrace':has_terrace,
            'garage':garage,
            'elevator':elevator,
            'airbnb_price_per_night':airbnb_price_per_night,
            'neighbourhood': neighbourhood,
            'district': district
        }
        # Define prediction function
        def house_price_prediction(input_data):
            input_df = pd.DataFrame(input_data, index = [0])
            print("Input DataFrame before prediction:")
            print(input_df)

            predictions = predict_model(model_pipeline, data=input_df)
            print("Columns in predictions DataFrame:", predictions.columns)
            print("Head of predictions DataFrame:\n", predictions.head())

            predicted_price = predictions['prediction_label'].values[0]
            return predicted_price
        
        prediction = house_price_prediction(input_data)
        st.write(f'Predicted Price: €{round(prediction,-3) - 40000:,.0f} - €{round(prediction,-3) + 40000:,.0f}')