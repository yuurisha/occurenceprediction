import pandas as pd
import requests
from datetime import datetime
import time
from typing import Dict, Optional

def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats and return YYYY-MM-DD format."""
    if pd.isna(date_str):
        return None
    
    # Handle date ranges (take the start date)
    if '/' in date_str:
        date_str = date_str.split('/')[0]
    
    # Remove timezone info and parse
    date_str = date_str.replace('T', ' ').split('+')[0].split('Z')[0]
    
    try:
        # Try parsing with time
        dt = pd.to_datetime(date_str)
        return dt.strftime('%Y-%m-%d')
    except:
        return None

def fetch_weather_data(lat: float, lon: float, date: str) -> Dict:
    """
    Fetch historical weather data from Open-Meteo API.
    Returns temperature, precipitation, humidity, wind speed, etc.
    """
    base_url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': date,
        'end_date': date,
        'daily': [
            'temperature_2m_max',
            'temperature_2m_min',
            'temperature_2m_mean',
            'precipitation_sum',
            'rain_sum',
            'precipitation_hours',
            'windspeed_10m_max',
            'windgusts_10m_max',
            'sunshine_duration'
        ],
        'timezone': 'auto'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'daily' in data:
            daily_data = data['daily']
            return {
                'temperature_max_C': daily_data['temperature_2m_max'][0] if daily_data['temperature_2m_max'] else None,
                'temperature_min_C': daily_data['temperature_2m_min'][0] if daily_data['temperature_2m_min'] else None,
                'temperature_mean_C': daily_data['temperature_2m_mean'][0] if daily_data['temperature_2m_mean'] else None,
                'precipitation_mm': daily_data['precipitation_sum'][0] if daily_data['precipitation_sum'] else None,
                'rain_mm': daily_data['rain_sum'][0] if daily_data['rain_sum'] else None,
                'precipitation_hours': daily_data['precipitation_hours'][0] if daily_data['precipitation_hours'] else None,
                'windspeed_max_kmh': daily_data['windspeed_10m_max'][0] if daily_data['windspeed_10m_max'] else None,
                'windgusts_max_kmh': daily_data['windgusts_10m_max'][0] if daily_data['windgusts_10m_max'] else None,
                'sunshine_duration_s': daily_data['sunshine_duration'][0] if daily_data['sunshine_duration'] else None,
            }
        else:
            return {}
    except Exception as e:
        print(f"Error fetching weather for {lat}, {lon}, {date}: {str(e)}")
        return {}

def main():
    # Read the occurrence data
    print("Reading occurrence data...")
    df = pd.read_csv('cleaned_gbif_data.csv')
    print(f"Found {len(df)} occurrence records")
    
    # Parse dates
    print("Parsing dates...")
    df['parsed_date'] = df['eventDate'].apply(parse_date)
    
    # Remove records without valid dates
    df_valid = df[df['parsed_date'].notna()].copy()
    print(f"Records with valid dates: {len(df_valid)}")
    
    # Initialize weather columns
    weather_columns = [
        'temperature_max_C', 'temperature_min_C', 'temperature_mean_C',
        'precipitation_mm', 'rain_mm', 'precipitation_hours',
        'windspeed_max_kmh', 'windgusts_max_kmh', 'sunshine_duration_s'
    ]
    
    for col in weather_columns:
        df_valid[col] = None
    
    # Fetch weather data for each occurrence
    print("Fetching weather data...")
    total = len(df_valid)
    
    for idx, row in df_valid.iterrows():
        if idx % 10 == 0:
            print(f"Progress: {idx}/{total} ({idx/total*100:.1f}%)")
        
        weather = fetch_weather_data(
            row['decimalLatitude'],
            row['decimalLongitude'],
            row['parsed_date']
        )
        
        for key, value in weather.items():
            df_valid.at[idx, key] = value
        
        # Rate limiting: Open-Meteo allows ~10,000 requests/day
        # Add a small delay to be respectful
        time.sleep(0.1)
    
    # Save the results
    output_file = 'occurrence_data_with_weather.csv'
    df_valid.to_csv(output_file, index=False)
    print(f"\nComplete! Weather data saved to {output_file}")
    print(f"Total records processed: {len(df_valid)}")
    
    # Display summary statistics
    print("\n--- Weather Data Summary ---")
    print(df_valid[weather_columns].describe())

if __name__ == "__main__":
    main()
