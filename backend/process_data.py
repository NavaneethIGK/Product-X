import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# Load the 1M shipment dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'shipment_data_1M.csv')
print(f"Loading CSV from {csv_path}...")
df = pd.read_csv(csv_path)

# Convert date columns
df['departed_at'] = pd.to_datetime(df['departed_at'])
df['expected_arrival'] = pd.to_datetime(df['expected_arrival'])
df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')

# Calculate transit time and delay
df['expected_transit_days'] = (df['expected_arrival'] - df['departed_at']).dt.days
df['actual_transit_days'] = (df['arrived_at'] - df['departed_at']).dt.days
df['delay_days'] = df['actual_transit_days'] - df['expected_transit_days']
df['is_delayed'] = (df['delay_days'] > 0) & (df['arrived_at'].notna())

print("\n=== Dataset Summary ===")
print(f"Total shipments: {len(df):,}")
print(f"Arrived: {df['arrived_at'].notna().sum():,} ({df['arrived_at'].notna().sum()/len(df)*100:.1f}%)")
print(f"In Transit: {df['arrived_at'].isna().sum():,} ({df['arrived_at'].isna().sum()/len(df)*100:.1f}%)")
print(f"Delayed shipments: {df['is_delayed'].sum():,} ({df['is_delayed'].sum()/len(df)*100:.1f}%)")

# Route analysis (source-destination pairs)
df['route'] = df['source_location'] + '->' + df['destination_location']
route_stats = df[df['arrived_at'].notna()].groupby('route').agg({
    'expected_transit_days': 'mean',
    'actual_transit_days': 'mean',
    'delay_days': 'mean',
    'is_delayed': 'sum',
    'shipment_id': 'count'
}).round(2)
route_stats.columns = ['expected_days', 'actual_days', 'avg_delay_days', 'delayed_count', 'total_count']
route_stats['delay_rate'] = (route_stats['delayed_count'] / route_stats['total_count'] * 100).round(2)
route_stats = route_stats.sort_values('delay_rate', ascending=False)

print("\n=== Top Routes by Delay Rate ===")
print(route_stats.head(10))

# Location pair analysis
df['location_pair'] = df['source_location'] + '->' + df['destination_location']
location_delays = df[df['arrived_at'].notna()].groupby('location_pair').agg({
    'delay_days': 'mean',
    'is_delayed': lambda x: (x.sum() / len(x) * 100)
}).round(2)
location_delays.columns = ['avg_delay', 'delay_percentage']
location_delays = location_delays.sort_values('delay_percentage', ascending=False)

# SKU analysis
sku_stats = df[df['arrived_at'].notna()].groupby('sku').agg({
    'delay_days': 'mean',
    'is_delayed': lambda x: (x.sum() / len(x) * 100),
    'quantity': 'mean'
}).round(2)
sku_stats.columns = ['avg_delay', 'delay_percentage', 'avg_quantity']
sku_stats = sku_stats[sku_stats['delay_percentage'] > 30].sort_values('delay_percentage', ascending=False)

print("\n=== SKUs with >30% Delay Rate ===")
print(sku_stats.head(10))

# Global metrics
global_metrics = {
    'total_shipments': int(len(df)),
    'on_time_percentage': float(((len(df) - df['is_delayed'].sum()) / len(df) * 100).round(2)),
    'delay_percentage': float((df['is_delayed'].sum() / len(df) * 100).round(2)),
    'average_delay_days': float(df[df['is_delayed']]['delay_days'].mean().round(2)),
    'maximum_delay_days': int(df['delay_days'].max()),
    'median_transit_days': int(df[df['arrived_at'].notna()]['actual_transit_days'].median())
}

print("\n=== Global Metrics ===")
for k, v in global_metrics.items():
    print(f"{k}: {v}")

# ETA Model: Simple regression-based model
# For each route, calculate baseline expected days and variance
eta_model = {}
for route, group in df[df['arrived_at'].notna()].groupby('route'):
    actual_days = group['actual_transit_days'].values
    eta_model[route] = {
        'baseline_days': float(group['actual_transit_days'].mean().round(2)),
        'std_dev': float(group['actual_transit_days'].std().round(2)),
        'samples': int(len(group)),
        'delay_rate': float((group['is_delayed'].sum() / len(group) * 100).round(2))
    }

# Save models to JSON
models = {
    'global_metrics': global_metrics,
    'eta_model': eta_model,
    'route_statistics': route_stats.head(20).to_dict(orient='index'),
    'sku_delays': sku_stats.head(20).to_dict(orient='index')
}

output_path = r'C:\Projects\Prototypes\Product X\product-x-dashboard\public\models.json'
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, 'w') as f:
    json.dump(models, f, indent=2)

print(f"\nModels saved to {output_path}")

# Generate sample predictions for in-transit shipments
in_transit = df[df['arrived_at'].isna()].sample(min(100, len(df[df['arrived_at'].isna()]))).copy()
predictions = []

for _, row in in_transit.iterrows():
    route = row['route']
    if route in eta_model:
        baseline = eta_model[route]['baseline_days']
        std_dev = eta_model[route]['std_dev']
    else:
        baseline = df[df['arrived_at'].notna()]['actual_transit_days'].mean()
        std_dev = df[df['arrived_at'].notna()]['actual_transit_days'].std()
    
    predicted_arrival = row['departed_at'] + timedelta(days=baseline)
    confidence = min(95, max(60, 100 - (std_dev * 10)))
    
    predictions.append({
        'shipment_id': row['shipment_id'],
        'route': route,
        'departed_at': row['departed_at'].isoformat(),
        'expected_arrival': row['expected_arrival'].isoformat(),
        'predicted_arrival': predicted_arrival.isoformat(),
        'predicted_days': baseline,
        'confidence': round(confidence, 2),
        'delay_risk': 'HIGH' if std_dev > 5 else 'MEDIUM' if std_dev > 2 else 'LOW',
        'status': 'IN_TRANSIT'
    })

predictions_df = pd.DataFrame(predictions)
predictions_path = r'C:\Projects\Prototypes\Product X\product-x-dashboard\public\predictions.json'
predictions_df.to_json(predictions_path, orient='records', indent=2)

print(f"Sample predictions saved to {predictions_path}")
print("\n✅ Data processing complete!")
