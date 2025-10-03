#!/usr/bin/env python3
"""
Script to automatically add home_id parameter to all management_logger calls in routes.py
"""
import re

def update_logger_calls(file_path):
    """Update all management_logger calls to include home_id parameter"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Patterns for different log methods - we need to handle multi-line calls
    # Strategy: Find closing parenthesis and add home_id before it
    
    # Track statistics
    stats = {
        'log_room_change': 0,
        'log_user_change': 0,
        'log_device_action': 0,
        'log_automation_change': 0,
        'log_login': 0,
        'log_logout': 0,
        'log_event': 0
    }
    
    # Find all log calls that don't already have home_id
    # We'll search for patterns like: self.management_logger.log_XXX( ... )
    # and check if they already have home_id
    
    methods = ['log_room_change', 'log_user_change', 'log_device_action', 
               'log_automation_change', 'log_login', 'log_logout', 'log_event']
    
    for method in methods:
        # Pattern to match the method call and capture everything until the closing )
        # This handles multi-line calls
        pattern = rf'(self\.management_logger\.{method}\([^)]+\))'
        
        def replacer(match):
            call_text = match.group(1)
            
            # Check if already has home_id
            if 'home_id=' in call_text:
                return call_text  # Already updated
            
            # Find the closing parenthesis
            # Insert home_id before it
            # We need to find the last ) that closes the method call
            
            # Simple approach: replace the last ) with , home_id=session.get('current_home_id'))
            # But we need to handle indentation properly
            
            # Find position of last )
            last_paren_pos = call_text.rfind(')')
            if last_paren_pos == -1:
                return call_text  # Something wrong, don't modify
            
            # Check if there's a trailing comma or newline before the )
            before_paren = call_text[:last_paren_pos].rstrip()
            
            # Determine indentation from the line with the )
            lines = call_text[:last_paren_pos].split('\n')
            if len(lines) > 1:
                # Multi-line call - use indentation from last parameter line
                last_line = lines[-1]
                # Count leading spaces
                indent = len(last_line) - len(last_line.lstrip())
                # Use same indentation for home_id
                new_call = before_paren + ',\n' + ' ' * indent + 'home_id=session.get(\'current_home_id\')' + call_text[last_paren_pos:]
            else:
                # Single line call
                new_call = before_paren + ', home_id=session.get(\'current_home_id\')' + call_text[last_paren_pos:]
            
            stats[method] += 1
            return new_call
        
        # Apply replacement
        content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Updated {file_path}")
        print("\nStatistics:")
        for method, count in stats.items():
            if count > 0:
                print(f"  {method}: {count} calls updated")
        return True
    else:
        print("No changes needed")
        return False

if __name__ == '__main__':
    routes_path = r'c:\Users\pz_przybysz\Documents\git\Site_proj\app\routes.py'
    update_logger_calls(routes_path)
