#!/usr/bin/env python3

import time
from datetime import datetime, timezone
import orjson
from sysdiagnose.utils.base import Event

def benchmark_individual_operations():
    """Benchmark each operation in the format conversion separately"""
    
    # Sample data similar to real logarchive entries
    sample_entry = {
        'timestamp': '2024-01-09T11:53:42.123456+00:00',
        'eventMessage': 'Sample log message with some text',
        'category': 'system',
        'subsystem': 'com.apple.test',
        'processID': 1234,
        'threadID': 5678,
        'bootUUID': '12345678-1234-1234-1234-123456789012',
        'processImageUUID': '87654321-4321-4321-4321-210987654321',
        'processImagePath': '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation',
        'senderImagePath': '/usr/lib/system/libsystem_trace.dylib'
    }
    
    iterations = 100000
    print(f"Benchmarking {iterations:,} iterations of each operation:")
    print("=" * 60)
    
    # 1. Test datetime.fromisoformat
    start = time.time()
    for _ in range(iterations):
        dt = datetime.fromisoformat(sample_entry['timestamp'])
    iso_time = time.time() - start
    print(f"datetime.fromisoformat: {iso_time:.3f}s ({iso_time/iterations*1000:.4f}ms per call)")
    
    # 2. Test Event creation
    dt = datetime.fromisoformat(sample_entry['timestamp'])
    start = time.time()
    for _ in range(iterations):
        event = Event(
            datetime=dt,
            message=sample_entry.get('eventMessage', ''),
            module='logarchive',
            timestamp_desc='logarchive'
        )
    event_creation_time = time.time() - start
    print(f"Event creation: {event_creation_time:.3f}s ({event_creation_time/iterations*1000:.4f}ms per call)")
    
    # 3. Test dictionary operations (the mapper loop)
    event = Event(
        datetime=dt,
        message=sample_entry.get('eventMessage', ''),
        module='logarchive',
        timestamp_desc='logarchive'
    )
    
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
    
    start = time.time()
    for _ in range(iterations):
        entry_copy = sample_entry.copy()
        entry_copy.pop('eventMessage', None)
        entry_copy.pop('timestamp', None)
        
        for key, value in entry_copy.items():
            if key in mapper:
                new_key = mapper[key]
                if 'uuid' in new_key and isinstance(value, str):
                    event.data[new_key] = value.replace('-', '')
                else:
                    event.data[new_key] = value
            else:
                event.data[key] = value
    
    dict_ops_time = time.time() - start
    print(f"Dictionary operations: {dict_ops_time:.3f}s ({dict_ops_time/iterations*1000:.4f}ms per call)")
    
    # 4. Test Event.to_dict()
    start = time.time()
    for _ in range(iterations):
        result_dict = event.to_dict()
    to_dict_time = time.time() - start
    print(f"Event.to_dict(): {to_dict_time:.3f}s ({to_dict_time/iterations*1000:.4f}ms per call)")
    
    # 5. Test orjson.dumps
    result_dict = event.to_dict()
    start = time.time()
    for _ in range(iterations):
        json_bytes = orjson.dumps(result_dict)
    json_dumps_time = time.time() - start
    print(f"orjson.dumps(): {json_dumps_time:.3f}s ({json_dumps_time/iterations*1000:.4f}ms per call)")
    
    # 6. Test the full pipeline
    start = time.time()
    for _ in range(iterations):
        entry_copy = sample_entry.copy()
        
        # Convert time
        timestamp = datetime.fromisoformat(entry_copy['timestamp'])
        event = Event(
            datetime=timestamp,
            message=entry_copy.get('eventMessage', ''),
            module='logarchive',
            timestamp_desc='logarchive'
        )
        entry_copy.pop('eventMessage', None)
        entry_copy.pop('timestamp', None)

        for key, value in entry_copy.items():
            if key in mapper:
                new_key = mapper[key]
                if 'uuid' in new_key and isinstance(value, str):
                    event.data[new_key] = value.replace('-', '')
                else:
                    event.data[new_key] = value
            else:
                event.data[key] = value
        
        result_dict = event.to_dict()
        json_bytes = orjson.dumps(result_dict)
    
    full_pipeline_time = time.time() - start
    print(f"Full pipeline: {full_pipeline_time:.3f}s ({full_pipeline_time/iterations*1000:.4f}ms per call)")
    
    print("\n" + "=" * 60)
    print("BREAKDOWN ANALYSIS:")
    total_individual = iso_time + event_creation_time + dict_ops_time + to_dict_time + json_dumps_time
    print(f"Sum of individual ops: {total_individual:.3f}s")
    print(f"Full pipeline actual: {full_pipeline_time:.3f}s")
    print(f"Overhead: {full_pipeline_time - total_individual:.3f}s")
    
    print(f"\nPer-operation percentage of full pipeline:")
    print(f"  datetime.fromisoformat: {iso_time/full_pipeline_time*100:.1f}%")
    print(f"  Event creation: {event_creation_time/full_pipeline_time*100:.1f}%")
    print(f"  Dictionary operations: {dict_ops_time/full_pipeline_time*100:.1f}%")
    print(f"  Event.to_dict(): {to_dict_time/full_pipeline_time*100:.1f}%")
    print(f"  orjson.dumps(): {json_dumps_time/full_pipeline_time*100:.1f}%")
    
    # Extrapolate to 3.9M entries
    real_entries = 3_921_030
    estimated_time = (full_pipeline_time / iterations) * real_entries
    print(f"\nExtrapolated to {real_entries:,} entries: {estimated_time:.1f}s")

if __name__ == "__main__":
    benchmark_individual_operations()
