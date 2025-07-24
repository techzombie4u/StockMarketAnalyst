
"""
Stock Market Analyst - ML Models Module

Implements machine learning models:
1. LSTM for price regression
2. Random Forest for direction classification
"""

import numpy as np
import pandas as pd
import joblib
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
import os
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class MLModels:
    def __init__(self):
        self.lstm_model = None
        self.rf_model = None
        self.lstm_model_path = 'lstm_model.h5'
        self.rf_model_path = 'rf_model.joblib'
    
    def create_lstm_model(self, input_shape: Tuple[int, int]) -> Sequential:
        """Create LSTM model architecture"""
        try:
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Error creating LSTM model: {str(e)}")
            return None
    
    def train_lstm_model(self, X: np.ndarray, y: np.ndarray) -> bool:
        """Train LSTM model for price regression"""
        try:
            if X is None or y is None or len(X) == 0:
                logger.error("Invalid training data for LSTM")
                return False
            
            logger.info(f"Training LSTM model with {len(X)} samples...")
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Create model
            input_shape = (X.shape[1], X.shape[2])
            self.lstm_model = self.create_lstm_model(input_shape)
            
            if self.lstm_model is None:
                return False
            
            # Early stopping callback
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            )
            
            # Train model
            history = self.lstm_model.fit(
                X_train, y_train,
                epochs=20,
                batch_size=32,
                validation_data=(X_val, y_val),
                callbacks=[early_stopping],
                verbose=1
            )
            
            # Save model
            self.lstm_model.save(self.lstm_model_path)
            logger.info(f"LSTM model saved to {self.lstm_model_path}")
            
            # Print training results
            final_loss = history.history['loss'][-1]
            final_val_loss = history.history['val_loss'][-1]
            logger.info(f"LSTM Training - Loss: {final_loss:.4f}, Val Loss: {final_val_loss:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training LSTM model: {str(e)}")
            return False
    
    def train_rf_model(self, X: np.ndarray, y: np.ndarray) -> bool:
        """Train Random Forest model for direction classification"""
        try:
            if X is None or y is None or len(X) == 0:
                logger.error("Invalid training data for Random Forest")
                return False
            
            logger.info(f"Training Random Forest model with {len(X)} samples...")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Create and train model
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2
            )
            
            self.rf_model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.rf_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Random Forest Test Accuracy: {accuracy:.4f}")
            
            # Save model
            joblib.dump(self.rf_model, self.rf_model_path)
            logger.info(f"Random Forest model saved to {self.rf_model_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training Random Forest model: {str(e)}")
            return False
    
    def load_models(self) -> bool:
        """Load pre-trained models"""
        try:
            # Load LSTM model
            if os.path.exists(self.lstm_model_path):
                self.lstm_model = tf.keras.models.load_model(self.lstm_model_path)
                logger.info("LSTM model loaded successfully")
            else:
                logger.warning("LSTM model file not found")
                return False
            
            # Load Random Forest model
            if os.path.exists(self.rf_model_path):
                self.rf_model = joblib.load(self.rf_model_path)
                logger.info("Random Forest model loaded successfully")
            else:
                logger.warning("Random Forest model file not found")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False
    
    def predict_price(self, lstm_input: np.ndarray, current_price: float) -> Optional[float]:
        """Predict next day price using LSTM"""
        try:
            if self.lstm_model is None or lstm_input is None:
                return None
            
            # Make prediction (normalized)
            prediction_normalized = self.lstm_model.predict(lstm_input, verbose=0)[0][0]
            
            # Convert normalized prediction back to price
            # Simple approach: assume prediction is percentage change
            predicted_price = current_price * (1 + prediction_normalized)
            
            return float(predicted_price)
            
        except Exception as e:
            logger.error(f"Error predicting price: {str(e)}")
            return None
    
    def predict_direction(self, rf_input: np.ndarray) -> Optional[Dict]:
        """Predict price direction using Random Forest"""
        try:
            if self.rf_model is None or rf_input is None:
                return None
            
            # Make prediction
            direction = self.rf_model.predict(rf_input)[0]
            probabilities = self.rf_model.predict_proba(rf_input)[0]
            
            return {
                'direction': int(direction),  # 0 = DOWN, 1 = UP
                'direction_label': 'UP' if direction == 1 else 'DOWN',
                'confidence': float(max(probabilities)),
                'up_probability': float(probabilities[1]) if len(probabilities) > 1 else 0.5,
                'down_probability': float(probabilities[0]) if len(probabilities) > 0 else 0.5
            }
            
        except Exception as e:
            logger.error(f"Error predicting direction: {str(e)}")
            return None
    
    def train_models(self, training_data: Dict) -> bool:
        """Train both models with provided data"""
        try:
            logger.info("Starting model training process...")
            
            # Train LSTM model
            lstm_success = False
            if training_data['lstm']['X'] is not None and training_data['lstm']['y'] is not None:
                lstm_success = self.train_lstm_model(
                    training_data['lstm']['X'], 
                    training_data['lstm']['y']
                )
            
            # Train Random Forest model
            rf_success = False
            if training_data['rf']['X'] is not None and training_data['rf']['y'] is not None:
                rf_success = self.train_rf_model(
                    training_data['rf']['X'], 
                    training_data['rf']['y']
                )
            
            success = lstm_success and rf_success
            logger.info(f"Model training completed. LSTM: {lstm_success}, RF: {rf_success}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            return False

def main():
    """Test model training"""
    from data_loader import MLDataLoader
    
    # Test symbols
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'WIPRO', 'SBIN']
    
    # Create data loader
    data_loader = MLDataLoader()
    
    # Create dummy fundamentals data
    fundamentals_data = {
        symbol: {
            'pe_ratio': 20.0,
            'revenue_growth': 10.0,
            'earnings_growth': 8.0,
            'promoter_buying': False
        } for symbol in test_symbols
    }
    
    # Create training dataset
    training_data = data_loader.create_training_dataset(test_symbols, fundamentals_data)
    
    # Train models
    models = MLModels()
    success = models.train_models(training_data)
    
    if success:
        print("✅ Models trained successfully!")
    else:
        print("❌ Model training failed!")

if __name__ == "__main__":
    main()
