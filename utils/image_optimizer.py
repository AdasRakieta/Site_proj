"""
Image optimization utilities for profile pictures.
Handles compression, resizing, format conversion, and cleanup.
"""
import os
from PIL import Image
from typing import Tuple, Optional
from werkzeug.utils import secure_filename


# Image optimization settings
MAX_WIDTH = 800
MAX_HEIGHT = 800
JPEG_QUALITY = 85
WEBP_QUALITY = 80
DEFAULT_PROFILE_PICTURE = 'podstawowe.jpg'


def optimize_profile_picture(
    image_file, 
    upload_folder: str, 
    max_size: Tuple[int, int] = (MAX_WIDTH, MAX_HEIGHT),
    use_webp: bool = True
) -> str:
    """
    Optimize and save a profile picture.
    
    Args:
        image_file: FileStorage object from Flask request
        upload_folder: Absolute path to upload directory
        max_size: Maximum dimensions (width, height)
        use_webp: Convert to WebP format for better compression
    
    Returns:
        Relative URL path to saved image (e.g., 'static/profile_pictures/user123.webp')
    
    Raises:
        ValueError: If image cannot be processed
        OSError: If file cannot be saved
    """
    try:
        # Generate secure filename
        original_filename = secure_filename(image_file.filename)
        name, ext = os.path.splitext(original_filename)
        
        # Open and convert to RGB (handles RGBA, grayscale, etc.)
        img = Image.open(image_file)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if necessary (maintain aspect ratio)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Determine output format and filename
        if use_webp:
            output_ext = '.webp'
            save_kwargs = {'format': 'WEBP', 'quality': WEBP_QUALITY, 'method': 6}
        else:
            output_ext = '.jpg'
            save_kwargs = {'format': 'JPEG', 'quality': JPEG_QUALITY, 'optimize': True}
        
        output_filename = f"{name}{output_ext}"
        output_path = os.path.join(upload_folder, output_filename)
        
        # Save optimized image
        img.save(output_path, **save_kwargs)
        
        # Return relative URL path
        return f"static/profile_pictures/{output_filename}"
        
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")


def delete_old_profile_picture(old_picture_url: Optional[str], base_dir: str) -> bool:
    """
    Delete old profile picture from filesystem.
    
    Args:
        old_picture_url: URL path to old image (e.g., 'static/profile_pictures/old.jpg')
        base_dir: Application base directory (usually app root)
    
    Returns:
        True if deleted successfully, False otherwise
    """
    if not old_picture_url:
        return False
    
    # Don't delete default profile picture
    if DEFAULT_PROFILE_PICTURE in old_picture_url:
        return False
    
    try:
        # Convert URL path to filesystem path
        # Remove leading slash if present
        relative_path = old_picture_url.lstrip('/')
        file_path = os.path.join(base_dir, relative_path)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        # Log error but don't fail the upload
        print(f"Warning: Failed to delete old profile picture {old_picture_url}: {e}")
    
    return False


def get_image_info(image_path: str) -> dict:
    """
    Get information about an image file.
    
    Args:
        image_path: Absolute path to image file
    
    Returns:
        Dict with format, size, dimensions, file_size
    """
    try:
        img = Image.open(image_path)
        file_size = os.path.getsize(image_path)
        
        return {
            'format': img.format,
            'mode': img.mode,
            'width': img.width,
            'height': img.height,
            'file_size': file_size,
            'file_size_kb': round(file_size / 1024, 2)
        }
    except Exception as e:
        return {'error': str(e)}
