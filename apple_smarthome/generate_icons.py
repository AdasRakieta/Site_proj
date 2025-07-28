#!/usr/bin/env python3
"""
Icon Generator for Apple SmartHome PWA
Creates placeholder icons in various sizes required for iOS
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys

def create_icon(size, output_path):
    """Create a simple icon with the given size"""
    # Create a new image with a gradient background
    img = Image.new('RGB', (size, size), '#007AFF')
    draw = ImageDraw.Draw(img)
    
    # Create a simple house icon design
    # Background circle
    margin = size // 8
    circle_size = size - 2 * margin
    draw.ellipse([margin, margin, margin + circle_size, margin + circle_size], 
                 fill='#FFFFFF', outline='#007AFF', width=2)
    
    # House shape
    house_margin = size // 4
    house_size = size - 2 * house_margin
    house_x = house_margin
    house_y = house_margin
    
    # House base (rectangle)
    base_height = house_size // 2
    base_y = house_y + house_size - base_height
    draw.rectangle([house_x, base_y, house_x + house_size, house_y + house_size], 
                   fill='#007AFF')
    
    # House roof (triangle)
    roof_points = [
        (house_x + house_size // 2, house_y),  # Top point
        (house_x, house_y + house_size // 2),   # Left point
        (house_x + house_size, house_y + house_size // 2)  # Right point
    ]
    draw.polygon(roof_points, fill='#007AFF')
    
    # Door
    door_width = house_size // 4
    door_height = base_height // 2
    door_x = house_x + (house_size - door_width) // 2
    door_y = house_y + house_size - door_height
    draw.rectangle([door_x, door_y, door_x + door_width, door_y + door_height], 
                   fill='#FFFFFF')
    
    # Window
    if size >= 64:
        window_size = house_size // 6
        window_x = house_x + house_size // 4
        window_y = base_y + base_height // 4
        draw.rectangle([window_x, window_y, window_x + window_size, window_y + window_size], 
                       fill='#FFFFFF')
    
    return img

def generate_icons():
    """Generate all required icon sizes"""
    icons_dir = '/home/runner/work/Site_proj/Site_proj/apple_smarthome/static/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # Icon sizes for PWA and Apple Touch Icons
    icon_sizes = {
        # PWA manifest icons
        'icon-72x72.png': 72,
        'icon-96x96.png': 96,
        'icon-128x128.png': 128,
        'icon-144x144.png': 144,
        'icon-152x152.png': 152,
        'icon-192x192.png': 192,
        'icon-384x384.png': 384,
        'icon-512x512.png': 512,
        
        # Apple Touch Icons
        'apple-touch-icon-57x57.png': 57,
        'apple-touch-icon-60x60.png': 60,
        'apple-touch-icon-72x72.png': 72,
        'apple-touch-icon-76x76.png': 76,
        'apple-touch-icon-114x114.png': 114,
        'apple-touch-icon-120x120.png': 120,
        'apple-touch-icon-144x144.png': 144,
        'apple-touch-icon-152x152.png': 152,
        'apple-touch-icon-180x180.png': 180,
        
        # Favicons
        'favicon-16x16.png': 16,
        'favicon-32x32.png': 32,
        'favicon-48x48.png': 48,
        
        # Splash screens (simplified - just using largest icon)
        'splash-640x1136.png': 512,
        'splash-750x1334.png': 512,
        'splash-1125x2436.png': 512,
        'splash-1242x2208.png': 512,
        'splash-1536x2048.png': 512,
        'splash-1668x2224.png': 512,
        'splash-2048x2732.png': 512,
    }
    
    print("Generating icons...")
    
    for filename, size in icon_sizes.items():
        icon_path = os.path.join(icons_dir, filename)
        
        if filename.startswith('splash-'):
            # For splash screens, create a centered icon on colored background
            splash_parts = filename.replace('splash-', '').replace('.png', '').split('x')
            splash_width = int(splash_parts[0])
            splash_height = int(splash_parts[1])
            
            # Create splash screen
            splash = Image.new('RGB', (splash_width, splash_height), '#000000')
            icon = create_icon(size, None)
            
            # Center the icon
            x = (splash_width - size) // 2
            y = (splash_height - size) // 2
            splash.paste(icon, (x, y))
            splash.save(icon_path, 'PNG')
        else:
            # Create regular icon
            icon = create_icon(size, None)
            icon.save(icon_path, 'PNG')
        
        print(f"Created: {filename} ({size}x{size})")
    
    print(f"All icons generated in: {icons_dir}")

if __name__ == '__main__':
    try:
        generate_icons()
        print("✓ Icon generation completed successfully!")
    except ImportError:
        print("PIL (Pillow) not available. Creating placeholder files...")
        
        # Create placeholder files if PIL is not available
        icons_dir = '/home/runner/work/Site_proj/Site_proj/apple_smarthome/static/icons'
        os.makedirs(icons_dir, exist_ok=True)
        
        # Create empty placeholder files
        placeholder_files = [
            'icon-72x72.png', 'icon-96x96.png', 'icon-128x128.png', 'icon-144x144.png',
            'icon-152x152.png', 'icon-192x192.png', 'icon-384x384.png', 'icon-512x512.png',
            'apple-touch-icon-57x57.png', 'apple-touch-icon-60x60.png', 'apple-touch-icon-72x72.png',
            'apple-touch-icon-76x76.png', 'apple-touch-icon-114x114.png', 'apple-touch-icon-120x120.png',
            'apple-touch-icon-144x144.png', 'apple-touch-icon-152x152.png', 'apple-touch-icon-180x180.png',
            'favicon-16x16.png', 'favicon-32x32.png'
        ]
        
        for filename in placeholder_files:
            with open(os.path.join(icons_dir, filename), 'w') as f:
                f.write('placeholder')
        
        print("✓ Placeholder icon files created. Install Pillow to generate actual icons.")
    
    except Exception as e:
        print(f"Error generating icons: {e}")
        sys.exit(1)