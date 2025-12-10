#!/usr/bin/env python3
"""Test smart query engine"""

from smart_query_engine import smart_parse_intent, execute_smart_query, format_for_response

# Test queries
test_queries = [
    'which destination has less shipment',
    'top sources by shipment count',
    'show me the 5 SKUs with fewest orders',
    'most popular routes',
    'which 3 destinations have the least shipments',
]

print('=== SMART QUERY ENGINE TESTS ===\n')

for query in test_queries:
    print(f'📝 Query: {query}')
    
    # Parse intent
    intent = smart_parse_intent(query)
    print(f'  → Aggregation: {intent.aggregation.value}')
    print(f'  → Sort: {intent.sort_order.value}')
    print(f'  → Limit: {intent.limit}')
    
    # Execute query
    result = execute_smart_query(intent)
    print(f'  → Success: {result["success"]}')
    print(f'  → Records: {len(result.get("data", []))}')
    
    # Format response
    response = format_for_response(result)
    print(f'  → Response:\n{response}\n')
    print('-' * 70 + '\n')
