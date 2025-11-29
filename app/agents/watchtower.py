# app/agents/watchtower.py
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from neuralprophet import NeuralProphet
from app.agents.level3_base_agent import Level3Agent
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class WatchtowerAgent(Level3Agent):
    """Forecasting agent - predicts patient load using NeuralProphet"""
    
    def __init__(self):
        super().__init__("Watchtower")
        self.model = None
        self.historical_data = None
        self.load_model()
    
    def load_model(self):
        """Load or train NeuralProphet model"""
        try:
            # Try to load existing model
            self.model = NeuralProphet.load('models/patient_load_model.nprophet')
            logger.info("Loaded existing NeuralProphet model")
        except:
            # Train new model if none exists
            logger.info("Training new NeuralProphet model...")
            self.model = NeuralProphet(
                growth='linear',
                n_changepoints=10,
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode='additive'
            )
            
            # Add external regressors
            self.model.add_future_regressor('aqi')
            self.model.add_future_regressor('is_festival')
            self.model.add_future_regressor('epidemic_risk')
    
    async def forecast_patient_load(self, forecast_date: str) -> Dict:
        """Main forecasting function"""
        
        logger.info(f"Forecasting patient load for {forecast_date}")
        
        # Get external signals
        aqi_forecast = await self.get_aqi_forecast(forecast_date)
        is_festival = await self.check_festival_calendar(forecast_date)
        epidemic_risk = await self.detect_epidemic_signals()
        
        # Prepare dataframe for prediction
        future_df = pd.DataFrame({
            'ds': [pd.to_datetime(forecast_date)],
            'aqi': [aqi_forecast],
            'is_festival': [1 if is_festival else 0],
            'epidemic_risk': [epidemic_risk]
        })
        
        # Run model prediction
        # If model is not trained, use fallback prediction
        if self.model is None:
            logger.warning("Model not available, using fallback prediction")
            # Fallback: simple prediction based on external factors
            base_load = 100
            aqi_factor = aqi_forecast / 100  # Normalize AQI
            festival_factor = 1.2 if is_festival else 1.0
            epidemic_factor = 1 + (epidemic_risk * 0.3)
            
            predicted_load = int(base_load * festival_factor * epidemic_factor * (1 + aqi_factor * 0.1))
            confidence_interval = {
                'lower': int(predicted_load * 0.85),
                'upper': int(predicted_load * 1.15)
            }
            confidence = 0.7  # Lower confidence for fallback
        else:
            try:
                forecast = self.model.predict(future_df)
                predicted_load = int(forecast['yhat1'].iloc[0]) if 'yhat1' in forecast.columns else 100
                confidence_interval = {
                    'lower': int(forecast['yhat1_lower'].iloc[0]) if 'yhat1_lower' in forecast.columns else predicted_load - 15,
                    'upper': int(forecast['yhat1_upper'].iloc[0]) if 'yhat1_upper' in forecast.columns else predicted_load + 15
                }
                confidence = 1 - (confidence_interval['upper'] - confidence_interval['lower']) / max(predicted_load, 1)
            except Exception as e:
                logger.error(f"Model prediction failed: {e}. Using fallback.")
                # Fallback prediction
                base_load = 100
                aqi_factor = aqi_forecast / 100
                festival_factor = 1.2 if is_festival else 1.0
                epidemic_factor = 1 + (epidemic_risk * 0.3)
                predicted_load = int(base_load * festival_factor * epidemic_factor * (1 + aqi_factor * 0.1))
                confidence_interval = {
                    'lower': int(predicted_load * 0.85),
                    'upper': int(predicted_load * 1.15)
                }
                confidence = 0.7
        
        result = {
            'date': forecast_date,
            'predicted_load': predicted_load,
            'confidence': round(confidence, 2),
            'confidence_interval': confidence_interval,
            'drivers': self._identify_drivers(aqi_forecast, is_festival, epidemic_risk),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Forecast complete: {predicted_load} patients (confidence: {confidence:.2%})")
        
        return result
    
    async def get_aqi_forecast(self, date: str) -> float:
        """Fetch Air Quality Index forecast from external API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Example: Using OpenWeatherMap Air Pollution API
                api_key = os.getenv("OPENWEATHER_API_KEY")
                url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat=12.9716&lon=77.5946&appid={api_key}"
                
                async with session.get(url) as response:
                    data = await response.json()
                    # Extract AQI for the target date
                    target_timestamp = int(pd.to_datetime(date).timestamp())
                    
                    for item in data.get('list', []):
                        if abs(item['dt'] - target_timestamp) < 86400:  # Within 24 hours
                            return item['main']['aqi'] * 50  # Convert to 0-500 scale
                    
                    return 100  # Default moderate AQI
        except Exception as e:
            logger.warning(f"Failed to fetch AQI forecast: {e}. Using default.")
            return 100
    
    async def check_festival_calendar(self, date: str) -> bool:
        """Check if date is a major festival/holiday"""
        # Indian festivals and holidays
        festivals_2025 = [
            '2025-01-26',  # Republic Day
            '2025-03-14',  # Holi
            '2025-04-10',  # Eid al-Fitr
            '2025-08-15',  # Independence Day
            '2025-10-02',  # Gandhi Jayanti
            '2025-10-24',  # Diwali
            '2025-12-25',  # Christmas
        ]
        
        target_date = pd.to_datetime(date).strftime('%Y-%m-%d')
        return target_date in festivals_2025
    
    async def detect_epidemic_signals(self) -> float:
        """Detect epidemic/outbreak signals from news and health data"""
        try:
            # Example: Check Google Trends or health bulletins
            # For demo, we'll return a random risk score
            
            # In production, you'd query:
            # - Google Trends API
            # - WHO disease outbreak news
            # - Local health department bulletins
            
            # Placeholder implementation
            return np.random.uniform(0, 0.3)  # Low to moderate risk
            
        except Exception as e:
            logger.warning(f"Failed to detect epidemic signals: {e}")
            return 0.0
    
    def _identify_drivers(self, aqi: float, is_festival: bool, epidemic_risk: float) -> Dict:
        """Identify key drivers of patient load"""
        drivers = {}
        
        if aqi > 150:
            drivers['pollution'] = 'HIGH'
            drivers['aqi'] = aqi
        
        if is_festival:
            drivers['festival'] = True
        
        if epidemic_risk > 0.5:
            drivers['epidemic'] = 'ALERT'
            drivers['risk_score'] = epidemic_risk
        
        return drivers
    
    async def execute_action(self, action: Dict) -> Any:
        """Watchtower doesn't execute actions, only forecasts"""
        raise NotImplementedError("Watchtower is read-only - it only produces forecasts")
    
    async def verify_outcome(self, action: Dict, result: Dict) -> Dict:
        """Watchtower doesn't execute actions"""
        raise NotImplementedError("Watchtower doesn't execute actions")
    
    async def evaluate_forecast_accuracy(self, forecast_date: str, actual_load: int) -> Dict:
        """Evaluate accuracy of past forecast"""
        # Find historical forecast
        past_forecast = next(
            (f for f in self.action_history if f.get('date') == forecast_date),
            None
        )
        
        if not past_forecast:
            return {'error': 'No forecast found for this date'}
        
        predicted = past_forecast['predicted_load']
        error = abs(predicted - actual_load)
        error_pct = (error / actual_load) * 100
        
        return {
            'date': forecast_date,
            'predicted': predicted,
            'actual': actual_load,
            'error': error,
            'error_pct': round(error_pct, 2),
            'within_confidence_interval': (
                past_forecast['confidence_interval']['lower'] <= actual_load <= 
                past_forecast['confidence_interval']['upper']
            )
        }
