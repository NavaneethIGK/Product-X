#!/usr/bin/env python3
"""Diagnose US-LAX query issue"""

import pandas as pd
import json

print("=" * 70)
print("DIAGNOSTICS: US-LAX Query Issue")
print("=" * 70)

# Load CSV
print("\n1. Loading CSV...")
try:
    df = pd.read_csv('shipment_data_1M.csv')
    print(f"   ✓ Loaded {len(df):,} records")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Check columns
print("\n2. Checking columns...")
print(f"   Columns: {df.columns.tolist()}")
print(f"   Data types:\n{df.dtypes}")

# Check US-LAX data
print("\n3. Checking US-LAX data...")
us_lax_df = df[df['destination_location'] == 'US-LAX']
print(f"   Total shipments to US-LAX: {len(us_lax_df):,}")

if len(us_lax_df) > 0:
    print(f"\n   Sample US-LAX shipments:")
    for idx, row in us_lax_df.head(5).iterrows():
        print(f"   - SHP-ID: {row['shipment_id']}, SKU: {row['sku']}, Qty: {row['quantity']}, Status: {row['status']}")
else:
    print("   ✗ No US-LAX shipments found!")

# Check unique destinations
print(f"\n4. Unique destinations: {df['destination_location'].nunique()}")
print(f"   {sorted(df['destination_location'].unique())}")

# Test smart query
print("\n5. Testing smart query engine...")
try:
    from smart_query_engine import smart_parse_intent, execute_smart_query, format_for_response
    
    query = "how many shipment to destination towards US-LAX"
    print(f"   Query: {query}")
    
    intent = smart_parse_intent(query)
    print(f"   Intent: aggregation={intent.aggregation.value}, sort={intent.sort_order.value}")
    
    result = execute_smart_query(intent)
    print(f"   Result success: {result.get('success')}")
    print(f"   Data returned: {len(result.get('data', []))} records")
    print(f"   Summary: {result.get('summary')}")
    
    if result.get('data'):
        print(f"   First result: {result['data'][0]}")
        
except Exception as e:
    import traceback
    print(f"   ✗ Error: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)
