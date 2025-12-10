#!/usr/bin/env python3
"""
Quick test script to check if fixes work
"""
import sys
sys.path.insert(0, '.')

from query_engine import get_shipment_details

# Test query for SHP-0000000
result = get_shipment_details('SHP-0000000')

print(f"Query Type: {result.query_type}")
print(f"Error: {result.error}")
print(f"Summary: {result.summary}")

if result.data:
    print("\nData returned:")
    import json
    print(json.dumps(result.data[0], indent=2, default=str))
else:
    print("\nNo data returned")
