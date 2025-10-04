#!/usr/bin/env python3
"""
Find all management_logger calls that don't have home_id parameter
"""
import re

routes_file = r'c:\Users\pz_przybysz\Documents\git\Site_proj\app\routes.py'

with open(routes_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track current call
in_call = False
call_start_line = 0
call_lines = []
call_method = ""

missing_home_id = []

for i, line in enumerate(lines, 1):
    # Check if line starts a management_logger call
    if 'self.management_logger.log_' in line:
        in_call = True
        call_start_line = i
        call_lines = [line]
        # Extract method name
        match = re.search(r'log_\w+', line)
        if match:
            call_method = match.group(0)
    elif in_call:
        call_lines.append(line)
        # Check if call ends (closing parenthesis)
        if ')' in line:
            # Join all lines of the call
            full_call = ''.join(call_lines)
            # Check if home_id is present
            if 'home_id=' not in full_call:
                missing_home_id.append({
                    'line': call_start_line,
                    'method': call_method,
                    'preview': call_lines[0].strip()[:80]
                })
            in_call = False
            call_lines = []

print(f"Found {len(missing_home_id)} management_logger calls without home_id:\n")
for item in missing_home_id:
    print(f"Line {item['line']}: {item['method']}")
    print(f"  {item['preview']}")
    print()
