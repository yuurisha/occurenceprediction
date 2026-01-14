# AI Notification System

This notification system integrates with the AI prediction API to alert users about species occurrence predictions.

## Features

- **Real-time Alerts**: Notifications when AI predictions are made
- **Severity-Based**: Color-coded by risk level (High/Medium/Low)
- **User Preferences**: Respects user's notification settings in Firebase
- **Batch Summaries**: Aggregated notifications for grid analysis
- **Persistence**: Saves all predictions to Firestore for historical tracking

## Architecture

### Backend Components

1. **ai_notifications.py** - Core notification logic
   - `save_ai_prediction_to_firestore()` - Saves predictions to `ai_predictions` collection
   - `create_ai_prediction_alert()` - Creates user notifications based on preferences
   - `create_batch_prediction_summary()` - Creates summary for grid analyses

2. **api.py** - FastAPI integration
   - Conditional notification creation based on request flags
   - Saves predictions when `save_prediction=true`
   - Creates alerts when `create_notification=true`

### Frontend Components

1. **AINotificationBell.tsx** - Dedicated AI notification UI
   - Brain icon to distinguish from general notifications
   - Filters for AI-specific notification types
   - Displays confidence scores and risk levels
   - Shows batch analysis statistics

2. **MapViewerWithAI.tsx** - Map integration
   - Passes user ID to API for personalized notifications
   - Sets notification flags for center point clicks
   - Skips notifications for grid point analyses

3. **NotificationContext.tsx** - Shared notification state
   - Fetches all notification types including AI predictions
   - Provides `markAsRead()` and `markAllAsRead()` actions

## Notification Types

### 1. ai_prediction_alert
Single prediction alert for user-clicked locations.

**Firestore Structure:**
```javascript
{
  notificationID: string,
  userID: string,
  type: "ai_prediction_alert",
  title: string,
  description: string,
  severity: "high" | "medium" | "low",
  confidence: number,
  modelType: "XGBoost",
  predictionID: string,  // Reference to ai_predictions document
  createdAt: Timestamp,
  read: boolean
}
```

**Example:**
```
Title: High Risk Area Detected
Description: ML model predicts HIGH likelihood (89% confidence) for species occurrence at this location.
Severity: high
```

### 2. ai_batch_analysis
Summary notification for grid analyses.

**Firestore Structure:**
```javascript
{
  notificationID: string,
  userID: string,
  type: "ai_batch_analysis",
  title: "Grid Analysis Complete",
  description: string,
  highRiskCount: number,
  mediumRiskCount: number,
  lowRiskCount: number,
  totalPredictions: number,
  centerLatitude: number,
  centerLongitude: number,
  createdAt: Timestamp,
  read: boolean
}
```

## User Preferences

Notifications respect the `notificationPreferences` collection:

```javascript
{
  userID: string,
  aiPredictionAlerts: boolean,  // Enable/disable AI alerts
  // ... other preferences
}
```

If `aiPredictionAlerts` is `false` or missing, no notifications are created.

## API Usage

### Single Prediction with Notification

```bash
curl -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 14.5547,
    "longitude": 121.0244,
    "temperature": 28.5,
    "humidity": 75,
    "rainfall": 150,
    "is_tropical": 1,
    "user_id": "user123",
    "create_notification": true,
    "save_prediction": true
  }'
```

### Batch Prediction without Notification

```bash
curl -X POST "http://localhost:8001/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"latitude": 14.5547, "longitude": 121.0244, "temperature": 28.5, ...},
      {"latitude": 14.5548, "longitude": 121.0245, "temperature": 28.6, ...}
    ],
    "user_id": null,
    "create_notification": false,
    "save_prediction": false
  }'
```

## Testing

### Backend Test
```bash
cd ai-model
python test_notifications.py
```

This will test:
- Single prediction notifications
- Batch summary notifications
- Disabled notification handling

### Manual Testing

1. Start the API server:
   ```bash
   cd ai-model
   python api.py
   ```

2. Start the Next.js app:
   ```bash
   cd florai
   npm run dev
   ```

3. Navigate to `http://localhost:3000/Dashboard/ai`

4. Click on the map to trigger a prediction

5. Check the AI notification bell (brain icon) for new alerts

## Firebase Collections

### ai_predictions
Stores all AI predictions for historical tracking.

```javascript
{
  predictionID: string,
  userID: string,
  latitude: number,
  longitude: number,
  predictedClass: "Low" | "Medium" | "High",
  confidence: number,
  probabilities: {
    Low: number,
    Medium: number,
    High: number
  },
  weatherData: {
    temperature: number,
    humidity: number,
    rainfall: number,
    is_tropical: number,
    // ... other weather features
  },
  modelType: "XGBoost",
  timestamp: Timestamp
}
```

### notifications
Contains all notification types, including AI alerts.

```javascript
{
  notificationID: string,
  userID: string,
  type: "ai_prediction_alert" | "ai_batch_analysis" | ...,
  // ... type-specific fields
  createdAt: Timestamp,
  read: boolean
}
```

## Environment Variables

The notification system requires Firebase credentials:

```bash
# In ai-model/.env (if needed)
FIREBASE_SERVICE_ACCOUNT="../florai/model_server/serviceAccountKey.json"
```

## Troubleshooting

### Notifications not appearing

1. Check user preferences:
   ```javascript
   // In Firebase Console > Firestore > notificationPreferences
   // Ensure aiPredictionAlerts: true
   ```

2. Verify API is receiving user_id:
   ```bash
   # Check API logs for:
   # "Creating notification for user: <user_id>"
   ```

3. Check Firebase rules allow writes:
   ```javascript
   // Firestore Rules
   match /notifications/{notificationId} {
     allow write: if request.auth != null;
   }
   ```

### Predictions saved but no notifications

- The user may have disabled `aiPredictionAlerts` in preferences
- Check `create_notification=false` in API request
- Verify `NOTIFICATIONS_ENABLED=true` in api.py

### Frontend not displaying AI notifications

1. Check AINotificationBell filters:
   ```typescript
   // Should include both types:
   n.type === "ai_prediction_alert" || n.type === "ai_batch_analysis"
   ```

2. Verify NotificationContext is wrapping the app:
   ```tsx
   // In layout.tsx or _app.tsx
   <NotificationProvider>
     {children}
   </NotificationProvider>
   ```

## Configuration

### Disable Notifications Globally

In `api.py`:
```python
NOTIFICATIONS_ENABLED = False  # Set to False to disable
```

### Customize Notification Messages

Edit `ai_notifications.py`:
```python
def create_ai_prediction_alert(user_id, prediction_data, prediction_id=None):
    # Modify title and description here
    notification_data = {
        "title": f"Custom {severity_upper} Alert",  # Customize
        "description": f"Your custom message...",    # Customize
        # ...
    }
```

## Performance Considerations

- Notifications are created asynchronously in the API
- Grid analyses skip notifications for individual points (performance)
- Batch summaries provide aggregated insights instead
- All predictions can be queried from `ai_predictions` collection later

## Future Enhancements

- [ ] Email notifications for high-risk predictions
- [ ] Push notifications via FCM
- [ ] Notification history page in UI
- [ ] Prediction comparison over time
- [ ] Export predictions to CSV
- [ ] Notification scheduling (daily/weekly summaries)
