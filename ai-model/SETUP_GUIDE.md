# Complete Setup Guide - AI Prediction with Notifications

This guide walks you through setting up the complete AI prediction system with notifications.

## Prerequisites

- Python 3.8+
- Node.js 16+
- Firebase project with Firestore enabled
- Firebase service account key

## Step 1: Backend Setup

### 1.1 Install Python Dependencies

```bash
cd ai-model
pip install -r requirements.txt
```

**Key packages:**
- xgboost==2.0.3
- scikit-learn==1.8.0
- fastapi
- uvicorn
- firebase-admin
- python-dotenv

### 1.2 Verify Model Files

Ensure these files exist:
```
ai-model/
  ├── occurrence_model.pkl      # Trained XGBoost model
  ├── scaler.pkl                # Feature scaler
  ├── feature_columns.pkl       # Feature names
  └── serviceAccountKey.json    # Firebase credentials (copy from florai/model_server/)
```

If `serviceAccountKey.json` doesn't exist in ai-model, copy it:
```bash
# Windows
copy ..\florai\model_server\serviceAccountKey.json .\serviceAccountKey.json

# Linux/Mac
cp ../florai/model_server/serviceAccountKey.json ./serviceAccountKey.json
```

### 1.3 Test Notifications (Optional)

```bash
python test_notifications.py
```

Expected output:
```
✅ Single Prediction ................ PASSED
✅ Batch Summary .................... PASSED
✅ Disabled Notifications ........... PASSED
```

### 1.4 Start API Server

```bash
python api.py
```

Or use PowerShell script:
```powershell
.\start-api.ps1
```

Verify it's running:
```bash
curl http://localhost:8001/health
# Should return: {"status":"healthy","model_loaded":true}
```

## Step 2: Frontend Setup

### 2.1 Install Node Dependencies

```bash
cd florai
npm install
```

### 2.2 Verify Firebase Configuration

Check that `lib/firebaseConfig.ts` has your Firebase credentials:
```typescript
const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  // ...
};
```

### 2.3 Start Development Server

```bash
npm run dev
```

## Step 3: Firebase Configuration

### 3.1 Create Firestore Collections

In Firebase Console, create these collections (they'll auto-create on first use):

1. **notificationPreferences**
   - Used to store user notification settings
   - Required field: `aiPredictionAlerts: boolean`

2. **notifications**
   - Stores all notification types
   - Auto-created when first notification is sent

3. **ai_predictions**
   - Stores prediction history
   - Auto-created when first prediction is saved

### 3.2 Set Firestore Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User can read their own notifications
    match /notifications/{notificationId} {
      allow read: if request.auth != null && resource.data.userID == request.auth.uid;
      allow write: if request.auth != null;
    }
    
    // User can manage their notification preferences
    match /notificationPreferences/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // User can read their own predictions
    match /ai_predictions/{predictionId} {
      allow read: if request.auth != null && resource.data.userID == request.auth.uid;
      allow write: if request.auth != null;
    }
  }
}
```

### 3.3 Enable User Preferences

For each user, create a document in `notificationPreferences`:

**Document ID:** `<user_uid>`
**Data:**
```javascript
{
  userID: "<user_uid>",
  aiPredictionAlerts: true,  // Enable AI notifications
  // ... other preferences
}
```

You can do this manually in Firebase Console or through your app's settings page.

## Step 4: Testing the Complete Flow

### 4.1 Login to Your App

1. Navigate to `http://localhost:3000`
2. Login with your test account
3. Note your user ID (check browser console or Firebase Auth)

### 4.2 Enable Notifications for Test User

In Firebase Console:
1. Go to Firestore > `notificationPreferences`
2. Create document with ID = your user UID
3. Set field: `aiPredictionAlerts: true`

### 4.3 Test AI Predictions

1. Navigate to `http://localhost:3000/Dashboard/ai`
2. Click anywhere on the map
3. Wait for prediction to complete (~2-3 seconds)
4. Check the brain icon (AI notification bell) in the top right

### 4.4 Verify in Firebase

Check Firestore collections:

**notifications collection:**
```javascript
{
  notificationID: "auto-generated",
  userID: "your-user-id",
  type: "ai_prediction_alert",
  title: "High Risk Area Detected",
  description: "ML model predicts HIGH likelihood...",
  severity: "high",
  confidence: 0.89,
  read: false,
  createdAt: Timestamp
}
```

**ai_predictions collection:**
```javascript
{
  predictionID: "auto-generated",
  userID: "your-user-id",
  latitude: 14.5547,
  longitude: 121.0244,
  predictedClass: "High",
  confidence: 0.89,
  modelType: "XGBoost",
  timestamp: Timestamp
}
```

## Step 5: API Testing

### 5.1 Direct API Test

Test with curl:

```bash
# Single prediction with notification
curl -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 14.5547,
    "longitude": 121.0244,
    "temperature": 28.5,
    "humidity": 75,
    "rainfall": 150,
    "is_tropical": 1,
    "user_id": "YOUR_USER_ID_HERE",
    "create_notification": true,
    "save_prediction": true
  }'
```

Expected response:
```json
{
  "predicted_class": "High",
  "confidence": 0.89,
  "probabilities": {
    "Low": 0.05,
    "Medium": 0.06,
    "High": 0.89
  }
}
```

### 5.2 Test Without Notification

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
    "user_id": null,
    "create_notification": false,
    "save_prediction": false
  }'
```

## Troubleshooting

### API won't start

**Error:** `Port 8001 already in use`
```bash
# Windows - Kill process on port 8001
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Change port in api.py if needed
uvicorn.run(app, host="0.0.0.0", port=8002)  # Use 8002
# Then update MapViewerWithAI.tsx AI_MODEL_API constant
```

**Error:** `Firebase credentials not found`
```bash
# Verify path in ai_notifications.py
firebase_app.py or copy serviceAccountKey.json to ai-model/
```

### Notifications not appearing

**Check 1:** User preferences exist and `aiPredictionAlerts: true`
```javascript
// Firebase Console > notificationPreferences > <user_uid>
{
  aiPredictionAlerts: true
}
```

**Check 2:** API is receiving user_id
```bash
# In API logs, look for:
# "Creating notification for user: <user_id>"
```

**Check 3:** Frontend is passing user_id
```typescript
// In MapViewerWithAI.tsx, verify:
const userID = auth.currentUser?.uid;
// Should not be undefined
```

### Frontend errors

**Error:** `Module not found: AINotificationBell`
```bash
# Verify file exists:
florai/components/AINotificationBell.tsx

# Restart Next.js dev server
npm run dev
```

**Error:** `auth is not defined`
```bash
# Verify import in MapViewerWithAI.tsx:
import { auth } from "@/lib/firebaseConfig";
```

## Configuration Options

### Disable Notifications

In `api.py`:
```python
NOTIFICATIONS_ENABLED = False
```

### Change Notification Severity Thresholds

In `ai_notifications.py`:
```python
def create_ai_prediction_alert(user_id, prediction_data, prediction_id=None):
    # Modify severity logic
    if confidence > 0.85:  # Was 0.7
        severity = "high"
    elif confidence > 0.70:  # Was 0.4
        severity = "medium"
    # ...
```

### Customize UI Colors

In `AINotificationBell.tsx`:
```typescript
const getSeverityColor = (severity: string) => {
  switch (severity) {
    case "high":
      return "bg-red-100 border-red-300";  // Customize
    // ...
  }
};
```

## Next Steps

1. **Deploy to Production:**
   - Host API on cloud platform (AWS, Azure, GCP)
   - Deploy Next.js app to Vercel
   - Update CORS settings in api.py

2. **Add Features:**
   - Email notifications for high-risk areas
   - Push notifications via FCM
   - Prediction history page
   - Export predictions to CSV

3. **Improve Model:**
   - Collect more training data
   - Add new weather features
   - Experiment with different models
   - Implement model retraining pipeline

## Support

For issues or questions:
1. Check the logs (API console output)
2. Verify Firebase Console for data
3. Check browser console for frontend errors
4. Review NOTIFICATION_README.md for detailed docs

## File Structure Reference

```
ai-model/
  ├── api.py                          # FastAPI server
  ├── ai_notifications.py             # Notification logic
  ├── train_occurrence_model.py       # Model training
  ├── occurrence_model.pkl            # Trained model
  ├── test_notifications.py           # Test suite
  ├── NOTIFICATION_README.md          # Detailed docs
  └── SETUP_GUIDE.md                  # This file

florai/
  ├── components/
  │   ├── MapViewerWithAI.tsx        # Map with AI integration
  │   └── AINotificationBell.tsx     # AI notification UI
  ├── app/Dashboard/
  │   ├── DashboardClientWithAI.tsx  # Dashboard with AI bell
  │   └── ai/page.tsx                 # AI dashboard route
  └── context/
      └── NotificationContext.tsx    # Shared notification state
```
