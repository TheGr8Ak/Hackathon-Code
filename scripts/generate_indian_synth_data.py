"""
Generate synthetic Indian hospital data for training NeuralProphet model
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_synthetic_data(start_date='2023-01-01', end_date='2024-12-31'):
    """Generate 2 years of synthetic patient admission data"""
    
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)
    
    # Indian festivals (affect patient load)
    festivals = {
        '2023-01-26': 'Republic Day',
        '2023-03-08': 'Holi',
        '2023-04-14': 'Eid al-Fitr',
        '2023-08-15': 'Independence Day',
        '2023-10-02': 'Gandhi Jayanti',
        '2023-11-12': 'Diwali',
        '2023-12-25': 'Christmas',
        '2024-01-26': 'Republic Day',
        '2024-03-25': 'Holi',
        '2024-04-10': 'Eid al-Fitr',
        '2024-08-15': 'Independence Day',
        '2024-10-02': 'Gandhi Jayanti',
        '2024-11-01': 'Diwali',
        '2024-12-25': 'Christmas',
    }
    
    # Generate data
    data = []
    base_load = 80
    
    for i, date in enumerate(dates):
        # Base trend (slight increase over time)
        trend = base_load + (i / n_days) * 20
        
        # Weekly seasonality (higher on weekdays)
        day_of_week = date.weekday()
        weekly_factor = 1.1 if day_of_week < 5 else 0.9
        
        # Monthly seasonality (monsoon affects respiratory cases)
        month = date.month
        if month in [6, 7, 8, 9]:  # Monsoon months
            monsoon_factor = 1.15
        else:
            monsoon_factor = 1.0
        
        # Festival effect
        date_str = date.strftime('%Y-%m-%d')
        is_festival = 1 if date_str in festivals else 0
        festival_factor = 1.3 if is_festival else 1.0
        
        # AQI (simulated - higher in winter months due to stubble burning)
        if month in [10, 11, 12, 1, 2]:
            aqi = np.random.normal(180, 30)  # Higher in winter
        else:
            aqi = np.random.normal(120, 25)
        aqi = max(50, min(500, aqi))  # Clamp to valid range
        
        # AQI effect on patient load
        aqi_factor = 1 + (aqi - 100) / 500
        
        # Epidemic risk (random spikes)
        epidemic_risk = np.random.uniform(0, 0.3)
        if np.random.random() < 0.05:  # 5% chance of outbreak
            epidemic_risk = np.random.uniform(0.5, 0.8)
        epidemic_factor = 1 + (epidemic_risk * 0.4)
        
        # Calculate patient load
        patient_load = int(
            trend * 
            weekly_factor * 
            monsoon_factor * 
            festival_factor * 
            aqi_factor * 
            epidemic_factor * 
            np.random.normal(1.0, 0.1)  # Random noise
        )
        patient_load = max(20, min(300, patient_load))  # Clamp to reasonable range
        
        data.append({
            'ds': date,
            'y': patient_load,
            'aqi': aqi,
            'is_festival': is_festival,
            'epidemic_risk': epidemic_risk
        })
    
    df = pd.DataFrame(data)
    
    # Save to CSV
    output_path = 'data/patient_load_history.csv'
    os.makedirs('data', exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"✅ Generated {len(df)} days of synthetic data")
    print(f"   Date range: {start_date} to {end_date}")
    print(f"   Patient load range: {df['y'].min()} - {df['y'].max()}")
    print(f"   Saved to: {output_path}")
    
    return df

if __name__ == "__main__":
    print("Generating synthetic Indian hospital data...")
    df = generate_synthetic_data()
    print("\nSample data:")
    print(df.head(10))

