import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

df = pd.read_csv('occurrence_data_with_weather.csv')

def generate_pseudo_absences_fast(df, n_samples, min_distance_km=50):
    """
    Fast method: Geographic exclusion + Environmental bias
    Generates absences in ~seconds
    """
    absences = []
    
    # Geographic bounds (extend beyond existing data)
    lat_range = (df['decimalLatitude'].min() - 5, df['decimalLatitude'].max() + 5)
    lon_range = (df['decimalLongitude'].min() - 5, df['decimalLongitude'].max() + 5)
    
    # Calculate environmental ranges (5th and 95th percentiles)
    temp_range = (df['temperature_mean_C'].quantile(0.05), df['temperature_mean_C'].quantile(0.95))
    precip_range = (df['precipitation_mm'].quantile(0.05), df['precipitation_mm'].quantile(0.95))
    
    # For geographic distance checking
    presence_coords = df[['decimalLatitude', 'decimalLongitude']].values
    nbrs = NearestNeighbors(n_neighbors=1, metric='haversine').fit(np.radians(presence_coords))
    
    attempts = 0
    max_attempts = n_samples * 20
    
    print(f"Generating {n_samples} pseudo-absences...")
    print(f"Temperature range: {temp_range[0]:.1f}°C to {temp_range[1]:.1f}°C")
    print(f"Precipitation range: {precip_range[0]:.1f}mm to {precip_range[1]:.1f}mm")
    
    while len(absences) < n_samples and attempts < max_attempts:
        attempts += 1
        
        # Random location
        lat = np.random.uniform(*lat_range)
        lon = np.random.uniform(*lon_range)
        
        # Check distance from presences (convert km to radians)
        distances, _ = nbrs.kneighbors(np.radians([[lat, lon]]))
        distance_km = distances[0][0] * 6371  # Earth radius in km
        
        # Skip if too close to presence points (rough conversion: 1 degree ≈ 111km)
        if distance_km < (min_distance_km / 111):
            continue
        
        # Generate environmental conditions (biased towards unsuitable)
        # 70% chance of extreme conditions
        if np.random.random() < 0.7:
            # Unsuitable conditions
            temp = np.random.choice([
                np.random.uniform(temp_range[0] - 5, temp_range[0]),  # Too cold
                np.random.uniform(temp_range[1], temp_range[1] + 5)   # Too hot
            ])
            precip = np.random.choice([
                np.random.uniform(0, precip_range[0]),                # Too dry
                np.random.uniform(precip_range[1], precip_range[1] * 1.5)  # Too wet
            ])
        else:
            # Some normal conditions for realism
            temp = np.random.uniform(*temp_range)
            precip = np.random.uniform(*precip_range)
        
        # Generate other weather variables (simplified)
        temp_max = temp + np.random.uniform(2, 8)
        temp_min = temp - np.random.uniform(2, 8)
        wind = np.random.uniform(5, 40)
        sunshine = np.random.uniform(0, 43200)
        
        absences.append({
            'species': 'Mikania micrantha',
            'decimalLatitude': lat,
            'decimalLongitude': lon,
            'temperature_max_C': temp_max,
            'temperature_min_C': temp_min,
            'temperature_mean_C': temp,
            'precipitation_mm': max(0, precip),
            'rain_mm': max(0, precip),
            'precipitation_hours': np.random.uniform(0, 24),
            'windspeed_max_kmh': wind,
            'windgusts_max_kmh': wind * 1.5,
            'sunshine_duration_s': sunshine,
            'presence': 0
        })
        
        # Progress update
        if len(absences) % 50 == 0:
            print(f"  Generated {len(absences)}/{n_samples} absences...")
    
    return pd.DataFrame(absences)


# Generate absences (same number as presences)
print(f"\n{'='*60}")
print(f"Original presence data: {len(df)} samples")
print(f"{'='*60}\n")

pseudo_absences = generate_pseudo_absences_fast(df, len(df), min_distance_km=50)

# Add presence label to original data
df['presence'] = 1

# Combine
combined_data = pd.concat([df, pseudo_absences], ignore_index=True)
combined_data = combined_data.sample(frac=1, random_state=42)  # Shuffle

# Save
output_file = 'training_data_complete.csv'
combined_data.to_csv(output_file, index=False)

print(f"\n{'='*60}")
print(f"✓ Generated {len(pseudo_absences)} pseudo-absences")
print(f"✓ Total dataset: {len(combined_data)} samples")
print(f"✓ Balance: Presence={combined_data['presence'].sum()}, Absence={(combined_data['presence']==0).sum()}")
print(f"✓ Saved to: {output_file}")
print(f"{'='*60}")

# Show sample statistics
print("\nSample statistics:")
print("\nPresence samples (first 3):")
print(combined_data[combined_data['presence']==1][['decimalLatitude', 'decimalLongitude', 'temperature_mean_C', 'precipitation_mm']].head(3))
print("\nAbsence samples (first 3):")
print(combined_data[combined_data['presence']==0][['decimalLatitude', 'decimalLongitude', 'temperature_mean_C', 'precipitation_mm']].head(3))
