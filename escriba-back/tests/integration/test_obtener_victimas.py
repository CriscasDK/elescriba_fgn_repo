#!/usr/bin/env python3
"""Test script for obtener_victimas_paginadas function"""

import sys
sys.path.insert(0, '/home/lab4/scripts/documentos_judiciales')

from core.consultas import obtener_victimas_paginadas

print("=" * 60)
print("TEST: obtener_victimas_paginadas")
print("=" * 60)

try:
    print("\n1. Calling obtener_victimas_paginadas(page=1, page_size=20)...")
    result = obtener_victimas_paginadas(page=1, page_size=20)
    print(f"\n✅ Result type: {type(result)}")
    print(f"✅ Result: {result}")

    if isinstance(result, tuple) and len(result) == 2:
        victimas, total = result
        print(f"\n✅ Unpacked successfully:")
        print(f"   - victimas: {len(victimas)} items")
        print(f"   - total: {total}")
    else:
        print(f"\n❌ Expected tuple of 2 elements, got: {result}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
