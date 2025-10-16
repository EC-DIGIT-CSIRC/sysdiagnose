#!/usr/bin/env python3

import time
from datetime import datetime, timezone
import orjson
from sysdiagnose.utils.base import Event

# Cached timezone for optimization
UTC_TZ = timezone.utc
NANOSECONDS_TO_SECONDS = 1_000_000_000

def convert_unifiedlog_time_to_datetime_original(time_ns: int) -> datetime:
    """Original implementation"""
    return datetime.fromtimestamp(time_ns / 1000000000, tz=timezone.utc)

def convert_unifiedlog_time_to_datetime_optimized(time_ns: int) -> datetime:
    """Optimized: cached timezone + pre-calculated constant"""
    return datetime.fromtimestamp(time_ns / NANOSECONDS_TO_SECONDS, tz=UTC_TZ)

def convert_entry_to_unifiedlog_format_original(entry: dict) -> dict:
    '''Original convert_entry_to_unifiedlog_format from logarchive.py'''
    
    timestamp_desc = 'logarchive'
    module = 'logarchive'

    # already in the Mandiant unifiedlog format
    if 'event_type' in entry:
        timestamp = convert_unifiedlog_time_to_datetime_original(entry['time'])
        entry['datetime'] = timestamp.isoformat(timespec='microseconds')
        entry['timestamp'] = timestamp.timestamp()
        event = Event(
            datetime=timestamp,
            message=entry.get('message', ''),
            module=module,
            timestamp_desc=timestamp_desc,
            data=entry
        )
        return event.to_dict()

    mapper = {
        # our own fields
        'timestamp_desc': 'timestamp_desc',
        'module': 'module',
        # logarchive fields
        'creatorActivityID': 'activity_id',
        'messageType': 'log_type',
        'activityIdentifier': 'activity_id',
        'bootUUID': 'boot_uuid',   # remove - in the UUID
        'category': 'category',
        'eventMessage': 'message',
        'eventType': 'event_type',
        'formatString': 'raw_message',
        'processID': 'pid',
        'processImagePath': 'process',
        'processImageUUID': 'process_uuid',  # remove - in the UUID
        'senderImagePath': 'library',
        'senderImageUUID': 'library_uuid',   # remove - in the UUID
        'subsystem': 'subsystem',
        'threadID': 'thread_id',
        'timestamp': 'time',  # requires conversion
        'timezoneName': 'timezone_name',  # ignore timezone as time and timestamp are correct
        'userID': 'euid'
    }
    # convert time
    timestamp = datetime.fromisoformat(entry['timestamp'])
    event = Event(
        datetime=timestamp,
        message=entry.get('eventMessage', ''),
        module=module,
        timestamp_desc=timestamp_desc
    )
    entry.pop('eventMessage', None)
    entry.pop('timestamp', None)

    for key, value in entry.items():
        if key in mapper:
            new_key = mapper[key]
            if 'uuid' in new_key:  # remove - in UUID
                event.data[new_key] = value.replace('-', '') if isinstance(value, str) else value
            else:
                event.data[new_key] = value
        else:
            # keep the non-matching entries
            event.data[key] = value
    return event.to_dict()

def convert_entry_to_unifiedlog_format_optimized(entry: dict) -> dict:
    '''Optimized version with cached objects and faster operations'''
    
    timestamp_desc = 'logarchive'
    module = 'logarchive'

    # already in the Mandiant unifiedlog format
    if 'event_type' in entry:
        timestamp = convert_unifiedlog_time_to_datetime_optimized(entry['time'])
        entry['datetime'] = timestamp.isoformat(timespec='microseconds')
        entry['timestamp'] = timestamp.timestamp()
        event = Event(
            datetime=timestamp,
            message=entry.get('message', ''),
            module=module,
            timestamp_desc=timestamp_desc,
            data=entry
        )
        return event.to_dict()

    # Pre-compiled mapper for faster lookups
    mapper = {
        'timestamp_desc': 'timestamp_desc',
        'module': 'module',
        'creatorActivityID': 'activity_id',
        'messageType': 'log_type',
        'activityIdentifier': 'activity_id',
        'bootUUID': 'boot_uuid',
        'category': 'category',
        'eventMessage': 'message',
        'eventType': 'event_type',
        'formatString': 'raw_message',
        'processID': 'pid',
        'processImagePath': 'process',
        'processImageUUID': 'process_uuid',
        'senderImagePath': 'library',
        'senderImageUUID': 'library_uuid',
        'subsystem': 'subsystem',
        'threadID': 'thread_id',
        'timestamp': 'time',
        'timezoneName': 'timezone_name',
        'userID': 'euid'
    }
    
    # convert time
    timestamp = datetime.fromisoformat(entry['timestamp'])
    event = Event(
        datetime=timestamp,
        message=entry.get('eventMessage', ''),
        module=module,
        timestamp_desc=timestamp_desc
    )
    
    # Remove keys once to avoid repeated lookups
    entry.pop('eventMessage', None)
    entry.pop('timestamp', None)

    # Use dict.get() for faster lookups and pre-compile UUID check
    for key, value in entry.items():
        new_key = mapper.get(key)
        if new_key:
            if 'uuid' in new_key and isinstance(value, str):  # remove - in UUID
                event.data[new_key] = value.replace('-', '')
            else:
                event.data[new_key] = value
        else:
            # keep the non-matching entries
            event.data[key] = value
    return event.to_dict()

def create_sample_entries(count: int) -> list:
    """Create sample log entries similar to what logarchive processes"""
    entries = []
    
    # Sample Mandiant format entry
    mandiant_entry = {
        'event_type': 'log',
        'time': 1704801222123456789,  # nanosecond timestamp
        'message': 'Sample log message',
        'category': 'system',
        'subsystem': 'com.apple.test',
        'pid': 1234,
        'thread_id': 5678
    }
    
    # Sample native format entry
    native_entry = {
        'timestamp': '2024-01-09T11:53:42.123456+00:00',
        'eventMessage': 'Sample native log message',
        'category': 'system',
        'subsystem': 'com.apple.test',
        'processID': 1234,
        'threadID': 5678,
        'bootUUID': '12345678-1234-1234-1234-123456789012',
        'processImageUUID': '87654321-4321-4321-4321-210987654321'
    }
    
    # Mix of both types (roughly 50/50 like real data)
    for i in range(count):
        if i % 2 == 0:
            # Create a copy and vary some fields
            entry = mandiant_entry.copy()
            entry['time'] += i * 1000000  # vary timestamp
            entry['message'] = f'Sample log message {i}'
            entry['pid'] = 1234 + i
        else:
            entry = native_entry.copy()
            entry['eventMessage'] = f'Sample native log message {i}'
            entry['processID'] = 1234 + i
        
        entries.append(entry)
    
    return entries

def benchmark_format_conversion():
    """Benchmark the full format conversion process"""
    
    # Test with different sizes to see scaling
    test_sizes = [1000, 10000, 100000]
    
    for size in test_sizes:
        print(f"\n{'='*60}")
        print(f"BENCHMARKING {size:,} ENTRIES")
        print(f"{'='*60}")
        
        entries = create_sample_entries(size)
        
        methods = [
            ("Original", convert_entry_to_unifiedlog_format_original),
            ("Optimized", convert_entry_to_unifiedlog_format_optimized),
        ]
        
        results = {}
        
        for name, method in methods:
            start_time = time.time()
            
            for entry in entries:
                # Make a copy since the function modifies the entry
                entry_copy = entry.copy()
                result = method(entry_copy)
                # Simulate the JSON dumping that happens in the real code
                json_bytes = orjson.dumps(result)
            
            end_time = time.time()
            duration = end_time - start_time
            results[name] = duration
            
            per_entry = (duration / len(entries)) * 1000  # ms
            print(f"{name:15}: {duration:.3f}s total, {per_entry:.4f}ms per entry")
        
        if len(results) > 1:
            original_time = results["Original"]
            optimized_time = results["Optimized"]
            speedup = original_time / optimized_time
            time_saved = original_time - optimized_time
            print(f"\nSpeedup: {speedup:.2f}x faster")
            print(f"Time saved: {time_saved:.3f}s ({time_saved/original_time*100:.1f}%)")
            
            # Extrapolate to 3.9M entries (like in the real logarchive)
            real_entries = 3_921_030
            estimated_original = (original_time / size) * real_entries
            estimated_optimized = (optimized_time / size) * real_entries
            estimated_savings = estimated_original - estimated_optimized
            
            print(f"\nExtrapolated to 3.9M entries:")
            print(f"Original: {estimated_original:.1f}s")
            print(f"Optimized: {estimated_optimized:.1f}s") 
            print(f"Potential savings: {estimated_savings:.1f}s")

if __name__ == "__main__":
    benchmark_format_conversion()
