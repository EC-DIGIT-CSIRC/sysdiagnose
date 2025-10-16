#!/usr/bin/env python3

import time
from datetime import datetime, timezone
import orjson

# Current implementation from logarchive.py
def convert_unifiedlog_time_to_datetime_original(time_ns: int) -> datetime:
    """Original implementation"""
    timestamp = datetime.fromtimestamp(time_ns / 1000000000, tz=timezone.utc)
    return timestamp

# Optimized version 1: Pre-calculate divisor
NANOSECONDS_TO_SECONDS = 1_000_000_000

def convert_unifiedlog_time_to_datetime_v1(time_ns: int) -> datetime:
    """Optimized: use pre-calculated constant"""
    return datetime.fromtimestamp(time_ns / NANOSECONDS_TO_SECONDS, tz=timezone.utc)

# Optimized version 2: Use cached timezone
UTC_TZ = timezone.utc

def convert_unifiedlog_time_to_datetime_v2(time_ns: int) -> datetime:
    """Optimized: use cached timezone object"""
    return datetime.fromtimestamp(time_ns / NANOSECONDS_TO_SECONDS, tz=UTC_TZ)

# Optimized version 3: Use integer division and modulo for microseconds
def convert_unifiedlog_time_to_datetime_v3(time_ns: int) -> datetime:
    """Optimized: use integer arithmetic for microseconds"""
    # Keep the same precision as original by using float division
    return datetime.fromtimestamp(time_ns / NANOSECONDS_TO_SECONDS, tz=UTC_TZ)

# Optimized version 4: Avoid repeated timezone.utc creation
def convert_unifiedlog_time_to_datetime_v4(time_ns: int) -> datetime:
    """Most optimized: cached timezone + pre-calculated divisor"""
    return datetime.fromtimestamp(time_ns * 1e-9, tz=UTC_TZ)

def benchmark_timestamp_conversion():
    """Benchmark different timestamp conversion methods"""
    
    # Sample nanosecond timestamps (similar to what logarchive processes)
    test_timestamps = [
        1704801222000000000,  # 2024-01-09 14:33:42 UTC
        1704801223123456789,  # with nanoseconds
        1704801224987654321,
        1704801225555555555,
        1704801226111111111,
    ] * 1000  # 5000 timestamps total
    
    methods = [
        ("Original", convert_unifiedlog_time_to_datetime_original),
        ("V1: Pre-calc", convert_unifiedlog_time_to_datetime_v1),
        ("V2: Cached TZ", convert_unifiedlog_time_to_datetime_v2),
        ("V3: Same as V2", convert_unifiedlog_time_to_datetime_v3),
        ("V4: Multiply 1e-9", convert_unifiedlog_time_to_datetime_v4),
    ]
    
    print(f"Benchmarking {len(test_timestamps)} timestamp conversions...")
    print("=" * 60)
    
    results = {}
    
    for name, method in methods:
        start_time = time.time()
        
        for ts in test_timestamps:
            dt = method(ts)
            # Also test the common operations done in logarchive
            iso_str = dt.isoformat(timespec='microseconds')
            unix_ts = dt.timestamp()
        
        end_time = time.time()
        duration = end_time - start_time
        results[name] = duration
        
        per_conversion = (duration / len(test_timestamps)) * 1000  # ms
        print(f"{name:20}: {duration:.3f}s total, {per_conversion:.4f}ms per conversion")
    
    print("\n" + "=" * 60)
    print("SPEEDUP COMPARISON:")
    baseline = results["Original"]
    for name, duration in results.items():
        if name != "Original":
            speedup = baseline / duration
            print(f"{name:20}: {speedup:.2f}x faster")

def test_correctness():
    """Verify all methods produce the same results"""
    test_ts = 1704801222123456789
    
    methods = [
        convert_unifiedlog_time_to_datetime_original,
        convert_unifiedlog_time_to_datetime_v1,
        convert_unifiedlog_time_to_datetime_v2,
        convert_unifiedlog_time_to_datetime_v3,
        convert_unifiedlog_time_to_datetime_v4,
    ]
    
    results = []
    for method in methods:
        dt = method(test_ts)
        results.append({
            'datetime': dt,
            'iso': dt.isoformat(timespec='microseconds'),
            'timestamp': dt.timestamp(),
            'microsecond': dt.microsecond
        })
    
    print("CORRECTNESS TEST:")
    print("=" * 60)
    for i, result in enumerate(results):
        print(f"Method {i}: {result['iso']} (μs: {result['microsecond']})")
    
    # Check if all results are equivalent
    all_same = all(
        r['iso'] == results[0]['iso'] and 
        abs(r['timestamp'] - results[0]['timestamp']) < 0.000001
        for r in results
    )
    
    print(f"\nAll methods produce equivalent results: {all_same}")
    return all_same

if __name__ == "__main__":
    print("Testing correctness first...")
    if test_correctness():
        print("\n" + "=" * 60)
        benchmark_timestamp_conversion()
    else:
        print("ERROR: Methods produce different results!")
