import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Number of rows
n = 1_000_000

# Generate last 2 months date range
end_date = datetime.now()
start_date = end_date - timedelta(days=60)

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# Sample locations & SKUs
locations = ["IN-DEL", "IN-MUM", "TH-BKK", "SG-SIN", "US-LAX", "CN-SHZ", "DE-FRA", "UK-LON"]
skus = [f"SKU-{i:04d}" for i in range(1, 501)]

# Generate basic fields
shipment_ids = [f"SHP-{i:07d}" for i in range(n)]
source_locations = np.random.choice(locations, n)
destination_locations = np.random.choice(locations, n)

# Generate departed_at
departed_at_list = [
    random_date(start_date, end_date - timedelta(days=5))
    for _ in range(n)
]

# Expected arrival
expected_arrival_list = [
    d + timedelta(days=random.randint(3, 15)) for d in departed_at_list
]

# Arrived_at (70% arrived)
arrived_at_list = [
    d + timedelta(days=random.randint(3, 20)) if random.random() < 0.7 else None
    for d in departed_at_list
]

# Status
status_list = ["ARRIVED" if arr is not None else "IN_TRANSIT" for arr in arrived_at_list]

# SKU + quantity
sku_list = np.random.choice(skus, n)
quantity_list = np.random.randint(1, 500, n)

# Create DataFrame
df = pd.DataFrame({
    "shipment_id": shipment_ids,
    "source_location": source_locations,
    "destination_location": destination_locations,
    "departed_at": departed_at_list,
    "expected_arrival": expected_arrival_list,
    "arrived_at": arrived_at_list,
    "status": status_list,
    "sku": sku_list,
    "quantity": quantity_list
})

# Save file
filepath = r"C:\Projects\Prototypes\Product X\shipment_data_1M.csv"
df.to_csv(filepath, index=False)

print(f"Dataset saved to: {filepath}")
print(f"Total records: {len(df):,}")
print(f"File size: ~{len(df) * 200 / 1_000_000:.1f} MB")
