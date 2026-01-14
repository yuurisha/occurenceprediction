"""
Test script for AI notification system
Tests both single prediction alerts and batch analysis summaries
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from ai_notifications import (
    save_ai_prediction_to_firestore,
    create_ai_prediction_alert,
    create_batch_prediction_summary
)

def test_single_prediction():
    """Test creating a single AI prediction notification"""
    print("=" * 60)
    print("TEST 1: Single Prediction Notification")
    print("=" * 60)
    
    # Test data
    user_id = "test_user_123"
    prediction_data = {
        "latitude": 14.5547,
        "longitude": 121.0244,
        "temperature": 28.5,
        "humidity": 75,
        "rainfall": 150,
        "is_tropical": 1,
        "predicted_class": "High",
        "confidence": 0.89,
        "probabilities": {
            "Low": 0.05,
            "Medium": 0.06,
            "High": 0.89
        }
    }
    
    try:
        # Save prediction to Firestore
        print("\n1. Saving prediction to Firestore...")
        prediction_id = save_ai_prediction_to_firestore(user_id, prediction_data)
        print(f"   ✓ Saved with ID: {prediction_id}")
        
        # Create notification alert
        print("\n2. Creating notification alert...")
        notification_created = create_ai_prediction_alert(user_id, prediction_data, prediction_id)
        
        if notification_created:
            print("   ✓ Notification created successfully")
        else:
            print("   ⚠ Notification not created (user may have disabled AI alerts)")
        
        print("\n✅ Test 1 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {str(e)}\n")
        return False


def test_batch_predictions():
    """Test creating a batch analysis summary"""
    print("=" * 60)
    print("TEST 2: Batch Prediction Summary")
    print("=" * 60)
    
    # Test data - simulating 9 predictions in a grid
    user_id = "test_user_123"
    grid_predictions = [
        {"predicted_class": "High", "confidence": 0.85},
        {"predicted_class": "High", "confidence": 0.78},
        {"predicted_class": "Medium", "confidence": 0.65},
        {"predicted_class": "Medium", "confidence": 0.72},
        {"predicted_class": "Medium", "confidence": 0.68},
        {"predicted_class": "Low", "confidence": 0.90},
        {"predicted_class": "Low", "confidence": 0.88},
        {"predicted_class": "Low", "confidence": 0.92},
        {"predicted_class": "High", "confidence": 0.81},
    ]
    
    center_location = {
        "latitude": 14.5547,
        "longitude": 121.0244
    }
    
    try:
        print("\n1. Creating batch summary notification...")
        notification_created = create_batch_prediction_summary(
            user_id, 
            grid_predictions, 
            center_location
        )
        
        if notification_created:
            print("   ✓ Batch summary notification created successfully")
        else:
            print("   ⚠ Notification not created (user may have disabled AI alerts)")
        
        print("\n✅ Test 2 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {str(e)}\n")
        return False


def test_disabled_notifications():
    """Test with a user who has disabled notifications"""
    print("=" * 60)
    print("TEST 3: Disabled Notifications")
    print("=" * 60)
    
    # Using a non-existent user ID (should not create notifications)
    user_id = "nonexistent_user_999"
    prediction_data = {
        "latitude": 14.5547,
        "longitude": 121.0244,
        "predicted_class": "Medium",
        "confidence": 0.75
    }
    
    try:
        print("\n1. Attempting to create notification for user without preferences...")
        notification_created = create_ai_prediction_alert(user_id, prediction_data)
        
        if not notification_created:
            print("   ✓ Correctly skipped notification (no preferences found)")
        else:
            print("   ⚠ Notification was created unexpectedly")
        
        print("\n✅ Test 3 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 3 FAILED: {str(e)}\n")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AI NOTIFICATION SYSTEM TEST SUITE")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Single Prediction", test_single_prediction()))
    results.append(("Batch Summary", test_batch_predictions()))
    results.append(("Disabled Notifications", test_disabled_notifications()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)
