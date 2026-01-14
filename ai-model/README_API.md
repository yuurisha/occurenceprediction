# Mikania micrantha Occurrence Prediction API

FastAPI application for predicting species occurrence likelihood based on location and weather data.

## Setup

### 1. Install Dependencies

```powershell
cd "c:\Users\Yourisha\Documents\SEM 6\florai\ai-model"
pip install -r requirements.txt
```

Or if using the virtual environment:

```powershell
& "C:/Users/Yourisha/Documents/SEM 6/florai/florai/model_server/.venv/Scripts/pip.exe" install -r requirements.txt
```

### 2. Ensure Model Files Exist

Make sure these files are in the same directory:
- `occurrence_model.pkl`
- `scaler.pkl`
- `feature_columns.pkl`

(These are created by running the Jupyter notebook)

## Running the API

### Start the server:

```powershell
cd "c:\Users\Yourisha\Documents\SEM 6\florai\ai-model"
python api.py
```

Or with uvicorn directly:

```powershell
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### 1. Root Endpoint
**GET** `/`

Returns API information and available endpoints.

**Response:**
```json
{
  "message": "Mikania micrantha Occurrence Prediction API",
  "status": "active",
  "model_loaded": true,
  "endpoints": {
    "predict": "/predict",
    "health": "/health",
    "docs": "/docs"
  }
}
```

### 2. Health Check
**GET** `/health`

Check if the API and model are loaded correctly.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "scaler_loaded": true,
  "features_loaded": true
}
```

### 3. Predict Occurrence (Single)
**POST** `/predict`

Predict occurrence likelihood for a single location.

**Request Body:**
```json
{
  "latitude": 14.6,
  "longitude": 121.0,
  "temperatureMax": 32,
  "temperatureMin": 24,
  "precipitation": 15,
  "windSpeed": 12,
  "sunshineDuration": 36000,
  "rainHours": 8
}
```

**Response:**
```json
{
  "likelihood": "High",
  "confidence": 0.9743,
  "probabilities": {
    "Low": 0.0007,
    "Medium": 0.0249,
    "High": 0.9743
  },
  "location": {
    "latitude": 14.6,
    "longitude": 121.0
  },
  "weather_summary": {
    "temperature_max": 32,
    "temperature_min": 24,
    "temperature_mean": 28,
    "precipitation": 15,
    "wind_speed": 12
  }
}
```

### 4. Predict Occurrence (Batch)
**POST** `/predict/batch`

Predict occurrence likelihood for multiple locations.

**Request Body:**
```json
[
  {
    "latitude": 14.6,
    "longitude": 121.0,
    "temperatureMax": 32,
    "temperatureMin": 24,
    "precipitation": 15,
    "windSpeed": 12,
    "sunshineDuration": 36000,
    "rainHours": 8
  },
  {
    "latitude": 1.3,
    "longitude": 103.8,
    "temperatureMax": 31,
    "temperatureMin": 25,
    "precipitation": 8,
    "windSpeed": 10,
    "sunshineDuration": 28000,
    "rainHours": 4
  }
]
```

**Response:**
```json
{
  "count": 2,
  "predictions": [
    {
      "location": {"latitude": 14.6, "longitude": 121.0},
      "likelihood": "High",
      "confidence": 0.9743,
      "probabilities": {"Low": 0.0007, "Medium": 0.0249, "High": 0.9743}
    },
    {
      "location": {"latitude": 1.3, "longitude": 103.8},
      "likelihood": "Medium",
      "confidence": 0.6689,
      "probabilities": {"Low": 0.6689, "Medium": 0.0530, "High": 0.2781}
    }
  ]
}
```

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

Visit `http://localhost:8000/redoc` for ReDoc documentation.

## Testing the API

Run the test script:

```powershell
python test_api.py
```

Or use curl:

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 14.6,
    "longitude": 121.0,
    "temperatureMax": 32,
    "temperatureMin": 24,
    "precipitation": 15,
    "windSpeed": 12,
    "sunshineDuration": 36000,
    "rainHours": 8
  }'
```

## Frontend Integration Example

### JavaScript/TypeScript

```typescript
async function predictOccurrence(lat: number, lon: number, weatherData: any) {
  const response = await fetch('http://localhost:8000/predict', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      latitude: lat,
      longitude: lon,
      temperatureMax: weatherData.temp_max,
      temperatureMin: weatherData.temp_min,
      precipitation: weatherData.precipitation,
      windSpeed: weatherData.wind_speed,
      sunshineDuration: weatherData.sunshine,
      rainHours: weatherData.rain_hours || 0
    })
  });
  
  const result = await response.json();
  console.log('Prediction:', result.likelihood);
  console.log('Confidence:', result.confidence);
  return result;
}
```

### React Example

```jsx
const [prediction, setPrediction] = useState(null);

const handleMapClick = async (lat, lon) => {
  // 1. Fetch weather data from your weather API
  const weatherData = await fetchWeatherData(lat, lon);
  
  // 2. Send to prediction API
  const response = await fetch('http://localhost:8000/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude: lat,
      longitude: lon,
      temperatureMax: weatherData.temp_max,
      temperatureMin: weatherData.temp_min,
      precipitation: weatherData.precipitation,
      windSpeed: weatherData.wind_speed,
      sunshineDuration: weatherData.sunshine_duration,
      rainHours: weatherData.rain_hours
    })
  });
  
  const result = await response.json();
  setPrediction(result);
};
```

## Field Descriptions

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `latitude` | float | Latitude coordinate | -90 to 90 |
| `longitude` | float | Longitude coordinate | -180 to 180 |
| `temperatureMax` | float | Maximum temperature (°C) | Any |
| `temperatureMin` | float | Minimum temperature (°C) | Any |
| `precipitation` | float | Precipitation amount (mm) | ≥ 0 |
| `windSpeed` | float | Wind speed (km/h) | ≥ 0 |
| `sunshineDuration` | float | Sunshine duration (seconds) | ≥ 0 |
| `rainHours` | float | Hours of rain in a day | 0 to 24 |

## CORS Configuration

The API is configured to accept requests from any origin (`*`). For production, update the CORS settings in `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `422`: Validation error (invalid input data)
- `500`: Server error (model not loaded or prediction error)

Error response example:
```json
{
  "detail": "Prediction error: Invalid input data"
}
```
