import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_prediction():
    """Test prediction endpoint"""
    print("Testing prediction endpoint...")
    
    # Test case 1: Manila, Philippines (High likelihood)
    data = {
        "latitude": 14.6,
        "longitude": 121.0,
        "temperatureMax": 32,
        "temperatureMin": 24,
        "precipitation": 15,
        "windSpeed": 12,
        "sunshineDuration": 36000,
        "rainHours": 8
    }
    
    response = requests.post(f"{BASE_URL}/predict", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test case 2: Cold region (Low likelihood)
    data2 = {
        "latitude": 45.0,
        "longitude": 90.0,
        "temperatureMax": 15,
        "temperatureMin": 5,
        "precipitation": 2,
        "windSpeed": 20,
        "sunshineDuration": 25000,
        "rainHours": 1
    }
    
    response2 = requests.post(f"{BASE_URL}/predict", json=data2)
    print(f"Status: {response2.status_code}")
    print(f"Response: {json.dumps(response2.json(), indent=2)}\n")

def test_batch_prediction():
    """Test batch prediction endpoint"""
    print("Testing batch prediction endpoint...")
    
    data_list = [
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
    
    response = requests.post(f"{BASE_URL}/predict/batch", json=data_list)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

if __name__ == "__main__":
    print("="*60)
    print("API TESTING")
    print("="*60 + "\n")
    
    try:
        test_health()
        test_prediction()
        test_batch_prediction()
        
        print("="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
    except Exception as e:
        print(f"Error: {e}")
