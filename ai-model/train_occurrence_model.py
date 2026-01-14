import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
print("Loading data...")
df = pd.read_csv('pseudoabsence_data.csv')

# Create occurrence density/likelihood categories
def create_likelihood_labels(df, grid_size=0.5):
    """
    Create likelihood categories based on spatial density of occurrences
    grid_size: degrees (roughly 50km at equator)
    """
    # Create grid cells
    df['lat_grid'] = (df['decimalLatitude'] / grid_size).round() * grid_size
    df['lon_grid'] = (df['decimalLongitude'] / grid_size).round() * grid_size
    
    # Count presences in each grid cell
    grid_counts = df[df['presence'] == 1].groupby(['lat_grid', 'lon_grid']).size().reset_index(name='count')
    
    # Merge back to original data
    df = df.merge(grid_counts, on=['lat_grid', 'lon_grid'], how='left')
    df['count'] = df['count'].fillna(0)
    
    # Define likelihood categories based on occurrence density
    # Low: 0-1, Medium: 2-5, High: 6+
    def categorize_likelihood(row):
        if row['presence'] == 0:
            return 0  # Low (absence)
        elif row['count'] <= 1:
            return 0  # Low (isolated occurrence)
        elif row['count'] <= 5:
            return 1  # Medium
        else:
            return 2  # High
    
    df['likelihood'] = df.apply(categorize_likelihood, axis=1)
    
    return df

print("Creating likelihood labels...")
df = create_likelihood_labels(df)

# Feature engineering
print("Engineering features...")

# 1. Climate features
df['temp_range'] = df['temperature_max_C'] - df['temperature_min_C']
df['is_tropical'] = ((df['temperature_mean_C'] > 20) & 
                     (df['temperature_mean_C'] < 30)).astype(int)

# 2. Geographic features
df['lat_abs'] = df['decimalLatitude'].abs()
df['is_equatorial'] = (df['lat_abs'] < 10).astype(int)

# 3. Precipitation features
df['is_humid'] = (df['precipitation_mm'] > 10).astype(int)
df['rain_hours_ratio'] = df['precipitation_hours'] / 24

# 4. Interaction features
df['temp_precip_interaction'] = df['temperature_mean_C'] * df['precipitation_mm']

# Select features for model
feature_cols = [
    # Location
    'decimalLatitude', 'decimalLongitude',
    'lat_abs', 'is_equatorial',
    
    # Temperature
    'temperature_max_C', 'temperature_min_C', 'temperature_mean_C',
    'temp_range', 'is_tropical',
    
    # Precipitation
    'precipitation_mm', 'rain_mm', 'precipitation_hours',
    'is_humid', 'rain_hours_ratio',
    
    # Wind & Sunshine
    'windspeed_max_kmh', 'windgusts_max_kmh',
    'sunshine_duration_s',
    
    # Interaction
    'temp_precip_interaction'
]

X = df[feature_cols]
y = df['likelihood']

print(f"\nDataset shape: {X.shape}")
print(f"Likelihood distribution:\n{y.value_counts()}")
print(f"  0 (Low): {(y==0).sum()} samples")
print(f"  1 (Medium): {(y==1).sum()} samples")
print(f"  2 (High): {(y==2).sum()} samples")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale features
print("\nScaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train XGBoost model
print("\nTraining XGBoost model...")
model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='multi:softprob',  # For multi-class classification
    random_state=42,
    eval_metric='mlogloss',
    enable_categorical=False  # Ensure compatibility
)

model.fit(
    X_train_scaled, y_train,
    eval_set=[(X_test_scaled, y_test)],
    verbose=10
)

# Evaluate
print("\n" + "="*50)
print("MODEL EVALUATION")
print("="*50)

y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)

print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, 
                          target_names=['Low', 'Medium', 'High']))

# Confusion Matrix
print("\nConfusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
print(cm)

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Low', 'Medium', 'High'],
            yticklabels=['Low', 'Medium', 'High'])
plt.title('Confusion Matrix')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
print("✓ Confusion matrix saved to 'confusion_matrix.png'")

# Feature Importance
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 10 Important Features:")
print(feature_importance.head(10))

plt.figure(figsize=(10, 6))
plt.barh(feature_importance['feature'].head(15), 
         feature_importance['importance'].head(15))
plt.xlabel('Importance')
plt.title('Top 15 Feature Importances')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
print("✓ Feature importance saved to 'feature_importance.png'")

# Cross-validation
print("\nPerforming 5-fold cross-validation...")
cv_scores = cross_val_score(model, X_train_scaled, y_train, 
                            cv=5, scoring='accuracy')
print(f"CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

# Save model and scaler
print("\nSaving model and scaler...")
joblib.dump(model, 'occurrence_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(feature_cols, 'feature_columns.pkl')

print("\n✓ Model saved to 'occurrence_model.pkl'")
print("✓ Scaler saved to 'scaler.pkl'")
print("✓ Feature columns saved to 'feature_columns.pkl'")

# Sample predictions
print("\n" + "="*50)
print("SAMPLE PREDICTIONS")
print("="*50)

sample_indices = np.random.choice(len(X_test), 5, replace=False)
for idx in sample_indices:
    pred_class = y_pred[idx]
    pred_proba = y_pred_proba[idx]
    true_class = y_test.iloc[idx]
    
    likelihood_names = ['Low', 'Medium', 'High']
    print(f"\nLocation: ({X_test.iloc[idx]['decimalLatitude']:.2f}, "
          f"{X_test.iloc[idx]['decimalLongitude']:.2f})")
    print(f"  True: {likelihood_names[true_class]}")
    print(f"  Predicted: {likelihood_names[pred_class]}")
    print(f"  Probabilities - Low: {pred_proba[0]:.2%}, "
          f"Medium: {pred_proba[1]:.2%}, High: {pred_proba[2]:.2%}")

print("\n" + "="*50)
print("TRAINING COMPLETE!")
print("="*50)
