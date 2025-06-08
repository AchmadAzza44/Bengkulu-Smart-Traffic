import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TrafficMLModels:
    """Machine learning models for traffic prediction"""

    def __init__(self):
        self.feature_columns = [
            'hour', 'day_of_week', 'month', 'is_weekend', 'is_holiday',
            'weather_intensity', 'vehicle_count', 'congestion_ratio',
            'avg_speed', 'is_central', 'hour_weather_interaction',
            'road_type'  # Fitur baru
        ]
        self.target_column = 'traffic_level'
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)

    def _preprocess_data(self, df):
        """Preprocess the data for model training"""
        for column in [self.target_column, 'weather', 'road_type']:
            if column in df.columns:
                le = LabelEncoder()
                df[column] = le.fit_transform(df[column])
                self.label_encoders[column] = le

        X = df[self.feature_columns]
        numerical_cols = ['vehicle_count', 'congestion_ratio', 'avg_speed', 'hour_weather_interaction']
        X[numerical_cols] = self.scaler.fit_transform(X[numerical_cols])
        y = df[self.target_column]
        return X, y

    def train_models(self, traffic_data):
        """Train machine learning models and return evaluation metrics"""
        logging.info("🔧 Preparing features for ML models...")
        X, y = self._preprocess_data(traffic_data)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_test, average='weighted')
        cm = confusion_matrix(y_test, y_pred)

        # Validasi silang
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='accuracy')
        logging.info(f"✅ Model training completed with accuracy: {accuracy:.1%}, F1-score: {f1:.3f}")
        logging.info(f"Cross-validation scores: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        logging.info(f"Confusion Matrix:\n{cm}")

        return {'accuracy': accuracy, 'f1_score': f1, 'confusion_matrix': cm}

    def predict_traffic(self, location, future_time):
        """Predict traffic level for a given location and time"""
        if self.model is None:
            logging.error("❌ Model not trained yet")
            return None

        sample_data = pd.DataFrame({
            'hour': [future_time.hour],
            'day_of_week': [future_time.weekday()],
            'month': [future_time.month],
            'is_weekend': [1 if future_time.weekday() >= 5 else 0],
            'is_holiday': [1 if any((future_time.date() == holiday.date() for holiday in self.holidays)) else 0],
            'weather_intensity': [0],
            'vehicle_count': [100],
            'congestion_ratio': [0.5],
            'avg_speed': [40],
            'is_central': [1 if location in ['Simpang Lima', 'Mall Bengkulu', 'Masjid Jamik'] else 0],
            'hour_weather_interaction': [future_time.hour * 0],
            'road_type': ['arterial']  # Default
        })

        sample_X = sample_data[self.feature_columns]
        numerical_cols = ['vehicle_count', 'congestion_ratio', 'avg_speed', 'hour_weather_interaction']
        sample_X[numerical_cols] = self.scaler.transform(sample_X[numerical_cols])
        sample_X['road_type'] = self.label_encoders['road_type'].transform(sample_X['road_type'])

        predicted_class = self.model.predict(sample_X)[0]
        predicted_proba = self.model.predict_proba(sample_X)[0]
        confidence = np.max(predicted_proba)
        traffic_level = self.label_encoders[self.target_column].inverse_transform([predicted_class])[0]

        return {
            'location': location,
            'datetime': future_time,
            'predicted_level': traffic_level,
            'confidence': confidence
        }
