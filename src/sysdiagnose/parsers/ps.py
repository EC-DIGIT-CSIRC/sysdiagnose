#! /usr/bin/env python3

# For Python3
# Script to parse ps.txt to ease parsing
# Author: david@autopsit.org
# Improvements: https://linkedin.com/in/josemiguelsoriano
#

from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
from sysdiagnose.utils.misc import snake_case
import glob
import os
import re


class PsParser(BaseParserInterface):
    description = "Parsing ps.txt file"
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'ps.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        for log_file in self.get_log_files():
            return self.parse_file(log_file)
        return {'error': ['No ps.txt file present']}

    def parse_file(self, filename):
        result = []
        pid_to_process = {}  # Dictionary to store PID -> process_name mapping
        
        try:
            with open(filename, "r") as f:
                header = re.split(r"\s+", f.readline().strip())
                header_length = len(header)

                # Field name mapping for standardization
                field_mapping = {
                    'f': 'process_flags_bitmask',
                    'ni': 'nice_priority_adjustment', 
                    'pri': 'kernel_priority',
                    'prsna': 'process_resident_address',
                    'rss': 'physical_memory_kb',
                    'vsz': 'virtual_memory_kb',
                    'tt': 'controlling_terminal',
                    'wchan': 'kernel_wait_channel',
                    'uid': 'owner_user_id',
                    '%cpu': 'cpu_usage_percent',
                    '%mem': 'memory_usage_percent'
                }

                # First pass: parse all entries and build PID mapping
                entries = []
                for line in f:
                    patterns = line.strip().split(None, header_length - 1)
                    entry = {}
                    
                    # Process each column
                    for col in range(header_length):
                        original_col_name = snake_case(header[col])
                        # Use standardized name if available, otherwise use original
                        col_name = field_mapping.get(original_col_name, original_col_name)
                        
                        try:
                            entry[col_name] = int(patterns[col])
                            continue
                        except ValueError:
                            try:
                                entry[col_name] = float(patterns[col])
                            except ValueError:
                                entry[col_name] = patterns[col]

                    # Split command into process_name and process_args (keep original command)
                    command = entry.get('command', '')
                    if command:
                        # Split on first space - everything before is process_name, rest is args
                        command_parts = command.split(' ', 1)
                        process_name = command_parts[0]
                        
                        # Handle special case: process names ending with ':' (like sshd:, httpd:)
                        # This indicates a process title, not the actual executable name
                        if process_name.endswith(':') and len(process_name) > 1:
                            base_name = process_name[:-1]  # Remove the trailing colon
                            
                            # Heuristic mapping for common process titles to likely executable paths
                            # Based on typical Unix/Linux/macOS installations
                            process_title_mapping = {
                                'sshd': '/usr/sbin/sshd',
                                'httpd': '/usr/sbin/httpd',
                                'nginx': '/usr/sbin/nginx',
                                'postgres': '/usr/bin/postgres',
                                'mysqld': '/usr/sbin/mysqld',
                                'apache2': '/usr/sbin/apache2',
                                'sendmail': '/usr/sbin/sendmail',
                                'postfix': '/usr/sbin/postfix',
                                'dovecot': '/usr/sbin/dovecot',
                                'vsftpd': '/usr/sbin/vsftpd',
                                'proftpd': '/usr/sbin/proftpd',
                                'bind9': '/usr/sbin/named',
                                'named': '/usr/sbin/named',
                                'dhcpd': '/usr/sbin/dhcpd',
                                'ntpd': '/usr/sbin/ntpd',
                                'chronyd': '/usr/sbin/chronyd',
                                'systemd': '/sbin/systemd',
                                'kthreadd': '[kthreadd]',
                                'migration': '[migration]',
                                'rcu_gp': '[rcu_gp]',
                                'watchdog': '[watchdog]'
                            }
                            
                            # Try to resolve the process name, fallback to cleaned name
                            resolved_name = process_title_mapping.get(base_name, base_name)
                            entry['process_name'] = resolved_name
                            entry['process_name_resolved'] = resolved_name != base_name  # Flag indicating heuristic resolution
                            
                        else:
                            entry['process_name'] = process_name
                            entry['process_name_resolved'] = False
                        
                        entry['process_args'] = command_parts[1] if len(command_parts) > 1 else None
                    else:
                        entry['process_name'] = None
                        entry['process_args'] = None
                        entry['process_name_resolved'] = False

                    # Build PID -> process_name mapping for parent resolution
                    pid = entry.get('pid')
                    process_name = entry.get('process_name')
                    if pid is not None and process_name:
                        pid_to_process[pid] = process_name

                    entries.append(entry)

                # Second pass: resolve parent processes and add metadata
                for entry in entries:
                    # Resolve parent process name from PPID
                    ppid = entry.get('ppid')
                    if ppid is not None and ppid in pid_to_process:
                        entry['parent_process'] = pid_to_process[ppid]
                    else:
                        entry['parent_process'] = None

                    # Add original metadata
                    timestamp = self.sysdiagnose_creation_datetime
                    entry['timestamp_desc'] = 'sysdiagnose creation'
                    entry['timestamp'] = timestamp.timestamp()
                    entry['datetime'] = timestamp.isoformat(timespec='microseconds')
                    entry['message'] = f"Process {entry['command']} [{entry['pid']}] running as {entry['user']}"
                    entry['saf_module'] = self.module_name

                return entries
                
        except Exception:
            logger.exception("Could not parse ps.txt")
            return []

    def exclude_known_goods(processes: dict, known_good: dict) -> list[dict]:
        """
        Exclude known good processes from the given list of processes.

        Args:
            processes (dict): The output from parse_file() to check.
            known_good (dict): The output of parse_file() from a known good.

        Returns:
            dict: The updated list of processes with known good processes excluded.
        """

        known_good_cmd = [x['command'] for x in known_good]

        for proc in processes:
            if proc['command'] in known_good_cmd:
                processes.remove(proc)

        return processes
