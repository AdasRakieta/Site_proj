"""
File upload validation utilities
"""

def allowed_file(filename):
    """
    Check if file extension is allowed for upload.
    Accepts common image formats: PNG, JPG, JPEG, GIF, WebP
    """
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}
