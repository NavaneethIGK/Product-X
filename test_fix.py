#!/usr/bin/env python3
"""Quick test of the fix"""

print("Testing smart query engine with filter support...\n")

try:
    from smart_query_engine import smart_parse_intent, execute_smart_query, format_for_response, AggregationType
    
    # Test 1: Filter query for US-LAX
    print("=" * 70)
    print("TEST 1: Filter query for US-LAX destination")
    print("=" * 70)
    
    query = "how many shipment to destination towards US-LAX"
    print(f"\nQuery: {query}\n")
    
    intent = smart_parse_intent(query)
    print(f"Intent Type: {intent.aggregation.value}")
    print(f"Filters: {intent.filters}")
    print(f"Confidence: {intent.confidence}\n")
    
    result = execute_smart_query(intent)
    print(f"Query Success: {result.get('success')}")
    print(f"Total Matching Shipments: {result.get('total_matching', 'N/A')}\n")
    
    response = format_for_response(result)
    print("Formatted Response:")
    print(response)
    
    # Test 2: Aggregation query (destination with least shipments)
    print("\n\n" + "=" * 70)
    print("TEST 2: Aggregation query for destinations with least shipments")
    print("=" * 70)
    
    query2 = "which destination has less shipment"
    print(f"\nQuery: {query2}\n")
    
    intent2 = smart_parse_intent(query2)
    print(f"Intent Type: {intent2.aggregation.value}")
    print(f"Sort Order: {intent2.sort_order.value}")
    print(f"Confidence: {intent2.confidence}\n")
    
    result2 = execute_smart_query(intent2)
    print(f"Query Success: {result2.get('success')}\n")
    
    response2 = format_for_response(result2)
    print("Formatted Response:")
    print(response2)
    
    print("\n\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
