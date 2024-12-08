import requests
from opencage.geocoder import OpenCageGeocode
from geopy.distance import geodesic

# Hardcoded OpenCage API key
API_KEY = "46f6ec6a67a04a279a29e10a9ae7b28a"  


# Function to get coordinates using OpenCage Geocoder
def get_coordinates(address, api_key):
    geocoder = OpenCageGeocode(api_key)
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


from opencage.geocoder import OpenCageGeocode


def get_district_and_neighborhood(street, postal_code, city):
    address = f"{street}, {postal_code}, {city}"
    geocoder = OpenCageGeocode(api_key)
    result = geocoder.geocode(address)
    
    if result and len(result):
        components = result[0]['components']
        neighborhood = components.get('quarter')
        district = components.get('suburb')
        print(result)
        return district, neighborhood
    return None, None

# Example address
street = "Calle Serrano"
postal_code = "28001"
city = "Madrid"
address = f"{street}, {postal_code}, {city}"

# Get district and neighborhood
district, neighbourhood = get_district_and_neighborhood(street, postal_code,city)



