import pandas as pd
import json

# Read CSV
df = pd.read_csv('shipment_data_1M.csv')

# Print columns
print("CSV Columns:", df.columns.tolist())

# Get first row
first_row = df.iloc[0].to_dict()
print("\nFirst row:")
print(json.dumps(first_row, indent=2, default=str))

# Check SHP-0000000
matching = df[df['shipment_id'] == 'SHP-0000000']
if not matching.empty:
    print("\n\nSHP-0000000:")
    print(json.dumps(matching.iloc[0].to_dict(), indent=2, default=str))
else:
    print("\nSHP-0000000 not found")
    
# Show all shipment IDs starting with SHP-000000
print("\n\nShipments starting with SHP-000000:")
mask = df['shipment_id'].str.startswith('SHP-000000')
print(df[mask]['shipment_id'].head(10).tolist())
