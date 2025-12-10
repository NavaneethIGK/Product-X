#!/usr/bin/env python3
"""Test filter queries for locations"""

from smart_query_engine import smart_parse_intent, execute_smart_query, format_for_response
import json

test_queries = [
    "how many shipment to destination towards US-LAX",
    "shipments heading to US-LAX",
    "show shipments to IN-DEL",
    "orders from IN-MUM",
    "shipments originating from TH-BKK",
]

print("=" * 70)
print("TESTING FILTER QUERIES")
print("=" * 70)

for query in test_queries:
    print(f"\n📝 Query: {query}")
    
    # Parse intent
    intent = smart_parse_intent(query)
    print(f"  Intent: {intent.aggregation.value}")
    if intent.filters:
        print(f"  Filters: {intent.filters}")
    print(f"  Confidence: {intent.confidence}")
    
    # Execute query
    result = execute_smart_query(intent)
    print(f"  Success: {result.get('success')}")
    if result.get('success'):
        print(f"  Total Matching: {result.get('total_matching', 'N/A')}")
    
    # Format response
    response = format_for_response(result)
    print(f"  Response:\n{response}\n")
    print("-" * 70)

print("\nDone!")
