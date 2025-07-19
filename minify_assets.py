#!/usr/bin/env python3
"""
Asset minification script for Site_proj
Minifies CSS and JS files while preserving original functionality
"""
import os
import glob
from cssmin import cssmin
from jsmin import jsmin

def minify_css_files(base_dir):
    """Minify all CSS files in the static/css directory"""
    css_dir = os.path.join(base_dir, 'static', 'css')
    css_files = glob.glob(os.path.join(css_dir, '*.css'))
    
    total_original_size = 0
    total_minified_size = 0
    
    for css_file in css_files:
        # Skip already minified files
        if css_file.endswith('.min.css'):
            continue
            
        print(f"Minifying CSS: {os.path.basename(css_file)}")
        
        with open(css_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        minified_content = cssmin(original_content)
        
        # Create minified filename
        base_name = os.path.splitext(css_file)[0]
        minified_file = f"{base_name}.min.css"
        
        with open(minified_file, 'w', encoding='utf-8') as f:
            f.write(minified_content)
            
        original_size = len(original_content)
        minified_size = len(minified_content)
        compression_ratio = (1 - minified_size / original_size) * 100
        
        total_original_size += original_size
        total_minified_size += minified_size
        
        print(f"  {os.path.basename(css_file)}: {original_size} → {minified_size} bytes ({compression_ratio:.1f}% reduction)")
    
    return total_original_size, total_minified_size

def minify_js_files(base_dir):
    """Minify all JS files in the static/js directory"""
    js_dir = os.path.join(base_dir, 'static', 'js')
    js_files = glob.glob(os.path.join(js_dir, '*.js'))
    
    total_original_size = 0
    total_minified_size = 0
    
    for js_file in js_files:
        # Skip already minified files
        if js_file.endswith('.min.js'):
            continue
            
        print(f"Minifying JS: {os.path.basename(js_file)}")
        
        with open(js_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        try:
            minified_content = jsmin(original_content)
        except Exception as e:
            print(f"  Warning: Could not minify {os.path.basename(js_file)}: {e}")
            # If minification fails, just copy the original
            minified_content = original_content
        
        # Create minified filename
        base_name = os.path.splitext(js_file)[0]
        minified_file = f"{base_name}.min.js"
        
        with open(minified_file, 'w', encoding='utf-8') as f:
            f.write(minified_content)
            
        original_size = len(original_content)
        minified_size = len(minified_content)
        compression_ratio = (1 - minified_size / original_size) * 100
        
        total_original_size += original_size
        total_minified_size += minified_size
        
        print(f"  {os.path.basename(js_file)}: {original_size} → {minified_size} bytes ({compression_ratio:.1f}% reduction)")
    
    return total_original_size, total_minified_size

def main():
    """Main minification process"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Starting asset minification...")
    print("=" * 50)
    
    # Minify CSS files
    print("\nMinifying CSS files:")
    css_original, css_minified = minify_css_files(base_dir)
    
    # Minify JS files
    print("\nMinifying JS files:")
    js_original, js_minified = minify_js_files(base_dir)
    
    # Summary
    total_original = css_original + js_original
    total_minified = css_minified + js_minified
    total_savings = total_original - total_minified
    total_compression = (total_savings / total_original) * 100 if total_original > 0 else 0
    
    print("\n" + "=" * 50)
    print("MINIFICATION SUMMARY:")
    print(f"CSS: {css_original} → {css_minified} bytes ({((css_original - css_minified) / css_original * 100):.1f}% reduction)")
    print(f"JS:  {js_original} → {js_minified} bytes ({((js_original - js_minified) / js_original * 100):.1f}% reduction)")
    print(f"Total: {total_original} → {total_minified} bytes ({total_compression:.1f}% reduction)")
    print(f"Space saved: {total_savings} bytes ({total_savings / 1024:.1f} KB)")

if __name__ == "__main__":
    main()