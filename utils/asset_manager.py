"""
Asset Management for Site_proj

This file provides comprehensive asset management capabilities for the smart home application.
It handles CSS/JS minification, automatic serving of optimized assets, and build automation.

Features:
- Automatic CSS/JS minification with compression statistics
- Intelligent minified asset serving (falls back to original if minified unavailable)
- Watch mode for automatic re-minification during development
- Build integration for production deployments
- Asset optimization reporting and statistics

Minification Process:
The minification process is designed to be both manual and automatic:

MANUAL MINIFICATION:
- Run `python utils/asset_manager.py` to minify all assets
- Run `python utils/asset_manager.py --watch` for automatic re-minification during development
- Original files (style.css, app.js) remain unchanged and editable
- Minified files (*.min.css, *.min.js) are generated automatically

AUTOMATIC SERVING:
- The application automatically serves minified versions when available
- Falls back to original files if minified versions don't exist
- No manual intervention required for asset serving
- Transparent to the end user

File Updates:
- MANUAL: You edit the original files (style.css, app.js, etc.)
- AUTOMATIC: Minified files are generated/updated by running this script
- SERVING: The application automatically chooses the best version to serve

Dependencies:
    - cssmin: CSS minification
    - jsmin: JavaScript minification  
    - watchdog: File watching for development mode (optional)
"""
import os
import glob
import time
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime

# Optional dependencies for advanced features
try:
    from cssmin import cssmin
except ImportError:
    cssmin = None

try:
    from jsmin import jsmin
except ImportError:
    jsmin = None

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AssetStats:
    """Statistics for asset processing"""
    original_size: int
    minified_size: int
    compression_ratio: float
    files_processed: int


class AssetManager:
    """
    Comprehensive asset management for CSS and JavaScript files
    
    Handles minification, optimization, and serving of static assets.
    Provides both manual and automatic workflows for asset processing.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize asset manager
        
        Args:
            base_dir: Base directory containing static assets (defaults to current script directory)
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.base_dir = Path(base_dir)
        self.static_dir = self.base_dir / 'static'
        self.css_dir = self.static_dir / 'css'
        self.js_dir = self.static_dir / 'js'
        
        # Check for required dependencies
        self.cssmin_available = cssmin is not None
        self.jsmin_available = jsmin is not None
        
        if not self.cssmin_available:
            logger.warning("cssmin not available - CSS minification disabled")
        if not self.jsmin_available:
            logger.warning("jsmin not available - JS minification disabled")
        
        logger.info(f"AssetManager initialized for {self.base_dir}")
    
    def get_css_files(self) -> List[Path]:
        """
        Get list of CSS files to process
        
        Returns:
            List of CSS file paths (excludes already minified files)
        """
        if not self.css_dir.exists():
            logger.warning(f"CSS directory not found: {self.css_dir}")
            return []
        
        css_files = []
        for css_file in self.css_dir.glob('*.css'):
            # Skip already minified files
            if not css_file.name.endswith('.min.css'):
                css_files.append(css_file)
        
        return css_files
    
    def get_js_files(self) -> List[Path]:
        """
        Get list of JavaScript files to process
        
        Returns:
            List of JS file paths (excludes already minified files)
        """
        if not self.js_dir.exists():
            logger.warning(f"JS directory not found: {self.js_dir}")
            return []
        
        js_files = []
        for js_file in self.js_dir.glob('*.js'):
            # Skip already minified files
            if not js_file.name.endswith('.min.js'):
                js_files.append(js_file)
        
        return js_files
    
    def minify_css_file(self, css_file: Path) -> Tuple[bool, AssetStats]:
        """
        Minify a single CSS file
        
        Args:
            css_file: Path to CSS file to minify
            
        Returns:
            Tuple of (success, AssetStats)
        """
        if not self.cssmin_available:
            logger.error("cssmin not available for CSS minification")
            return False, AssetStats(0, 0, 0.0, 0)
        
        try:
            logger.info(f"Minifying CSS: {css_file.name}")
            
            # Read original file
            with open(css_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Minify content
            minified_content = cssmin(original_content)
            
            # Create minified filename
            minified_file = css_file.with_suffix('.min.css')
            
            # Write minified file
            with open(minified_file, 'w', encoding='utf-8') as f:
                f.write(minified_content)
            
            # Calculate statistics
            original_size = len(original_content)
            minified_size = len(minified_content)
            compression_ratio = (1 - minified_size / original_size) * 100 if original_size > 0 else 0
            
            stats = AssetStats(
                original_size=original_size,
                minified_size=minified_size,
                compression_ratio=compression_ratio,
                files_processed=1
            )
            
            logger.info(f"  {css_file.name}: {original_size} → {minified_size} bytes ({compression_ratio:.1f}% reduction)")
            return True, stats
            
        except Exception as e:
            logger.error(f"Failed to minify CSS {css_file.name}: {e}")
            return False, AssetStats(0, 0, 0.0, 0)
    
    def minify_js_file(self, js_file: Path) -> Tuple[bool, AssetStats]:
        """
        Minify a single JavaScript file
        
        Args:
            js_file: Path to JS file to minify
            
        Returns:
            Tuple of (success, AssetStats)
        """
        if not self.jsmin_available:
            logger.error("jsmin not available for JS minification")
            return False, AssetStats(0, 0, 0.0, 0)
        
        try:
            logger.info(f"Minifying JS: {js_file.name}")
            
            # Read original file
            with open(js_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Minify content with error handling
            try:
                minified_content = jsmin(original_content)
            except Exception as e:
                logger.warning(f"JS minification failed for {js_file.name}: {e}")
                # If minification fails, copy original content
                minified_content = original_content
            
            # Create minified filename
            minified_file = js_file.with_suffix('.min.js')
            
            # Write minified file
            with open(minified_file, 'w', encoding='utf-8') as f:
                f.write(minified_content)
            
            # Calculate statistics
            original_size = len(original_content)
            minified_size = len(minified_content)
            compression_ratio = (1 - minified_size / original_size) * 100 if original_size > 0 else 0
            
            stats = AssetStats(
                original_size=original_size,
                minified_size=minified_size,
                compression_ratio=compression_ratio,
                files_processed=1
            )
            
            logger.info(f"  {js_file.name}: {original_size} → {minified_size} bytes ({compression_ratio:.1f}% reduction)")
            return True, stats
            
        except Exception as e:
            logger.error(f"Failed to minify JS {js_file.name}: {e}")
            return False, AssetStats(0, 0, 0.0, 0)
    
    def minify_all_assets(self) -> Dict[str, AssetStats]:
        """
        Minify all CSS and JavaScript assets
        
        Returns:
            Dictionary with minification statistics for each asset type
        """
        logger.info("Starting asset minification process")
        
        # Initialize statistics
        css_stats = AssetStats(0, 0, 0.0, 0)
        js_stats = AssetStats(0, 0, 0.0, 0)
        
        # Process CSS files
        css_files = self.get_css_files()
        if css_files:
            logger.info(f"Processing {len(css_files)} CSS files")
            for css_file in css_files:
                success, file_stats = self.minify_css_file(css_file)
                if success:
                    css_stats.original_size += file_stats.original_size
                    css_stats.minified_size += file_stats.minified_size
                    css_stats.files_processed += 1
        else:
            logger.info("No CSS files found to process")
        
        # Process JS files
        js_files = self.get_js_files()
        if js_files:
            logger.info(f"Processing {len(js_files)} JS files")
            for js_file in js_files:
                success, file_stats = self.minify_js_file(js_file)
                if success:
                    js_stats.original_size += file_stats.original_size
                    js_stats.minified_size += file_stats.minified_size
                    js_stats.files_processed += 1
        else:
            logger.info("No JS files found to process")
        
        # Calculate compression ratios
        if css_stats.original_size > 0:
            css_stats.compression_ratio = (1 - css_stats.minified_size / css_stats.original_size) * 100
        
        if js_stats.original_size > 0:
            js_stats.compression_ratio = (1 - js_stats.minified_size / js_stats.original_size) * 100
        
        logger.info("Asset minification completed")
        return {
            'css': css_stats,
            'js': js_stats
        }
    
    def print_summary(self, stats: Dict[str, AssetStats]):
        """
        Print minification summary
        
        Args:
            stats: Statistics from minification process
        """
        css_stats = stats['css']
        js_stats = stats['js']
        
        print("\n" + "=" * 60)
        print("ASSET MINIFICATION SUMMARY")
        print("=" * 60)
        
        if css_stats.files_processed > 0:
            print(f"CSS: {css_stats.original_size} → {css_stats.minified_size} bytes "
                  f"({css_stats.compression_ratio:.1f}% reduction)")
            print(f"     {css_stats.files_processed} files processed")
        else:
            print("CSS: No files processed")
        
        if js_stats.files_processed > 0:
            print(f"JS:  {js_stats.original_size} → {js_stats.minified_size} bytes "
                  f"({js_stats.compression_ratio:.1f}% reduction)")
            print(f"     {js_stats.files_processed} files processed")
        else:
            print("JS:  No files processed")
        
        # Total statistics
        total_original = css_stats.original_size + js_stats.original_size
        total_minified = css_stats.minified_size + js_stats.minified_size
        total_files = css_stats.files_processed + js_stats.files_processed
        
        if total_original > 0:
            total_compression = (1 - total_minified / total_original) * 100
            total_savings = total_original - total_minified
            
            print("-" * 60)
            print(f"Total: {total_original} → {total_minified} bytes ({total_compression:.1f}% reduction)")
            print(f"Space saved: {total_savings} bytes ({total_savings / 1024:.1f} KB)")
            print(f"Files processed: {total_files}")
        
        print("=" * 60)
    
    def clean_minified_assets(self):
        """
        Remove all minified asset files
        
        Useful for cleanup or forcing regeneration of all minified assets
        """
        logger.info("Cleaning minified assets")
        
        cleaned_count = 0
        
        # Clean CSS minified files
        for minified_file in self.css_dir.glob('*.min.css'):
            try:
                minified_file.unlink()
                logger.debug(f"Removed {minified_file.name}")
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to remove {minified_file.name}: {e}")
        
        # Clean JS minified files
        for minified_file in self.js_dir.glob('*.min.js'):
            try:
                minified_file.unlink()
                logger.debug(f"Removed {minified_file.name}")
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to remove {minified_file.name}: {e}")
        
        logger.info(f"Cleaned {cleaned_count} minified asset files")


def minified_url_for_helper(app):
    """
    Create a minified URL helper for Flask applications
    
    This function replaces Flask's url_for in templates to automatically
    serve minified assets when available, falling back to originals.
    
    Args:
        app: Flask application instance
        
    Returns:
        Custom url_for function for template use
    """
    from flask import url_for as original_url_for
    
    def minified_url_for(endpoint, **values):
        """
        Custom url_for function that serves minified assets when available
        Falls back to original if minified version doesn't exist
        """
        if endpoint == 'static' and 'filename' in values:
            filename = values['filename']
            
            # Check if it's a CSS or JS file
            if filename.endswith('.css') or filename.endswith('.js'):
                # Don't process already minified files
                if not filename.endswith('.min.css') and not filename.endswith('.min.js'):
                    # Create minified filename
                    name, ext = os.path.splitext(filename)
                    minified_filename = f"{name}.min{ext}"
                    
                    # Check if minified version exists
                    minified_path = os.path.join(app.static_folder, minified_filename)
                    if os.path.exists(minified_path):
                        values['filename'] = minified_filename
                        logger.debug(f"Serving minified asset: {minified_filename}")
                    else:
                        logger.debug(f"Minified asset not found, serving original: {filename}")
        
        return original_url_for(endpoint, **values)
    
    return minified_url_for


# Define AssetWatcher conditionally based on availability
if WATCHDOG_AVAILABLE:
    from watchdog.events import FileSystemEventHandler
    
    class AssetWatcher(FileSystemEventHandler):
        """
        File system watcher for automatic asset minification during development
        
        Watches for changes to CSS and JS files and automatically triggers
        minification when files are modified.
        """
        
        def __init__(self, asset_manager: AssetManager):
            """
            Initialize asset watcher
            
            Args:
                asset_manager: AssetManager instance for processing files
            """
            self.asset_manager = asset_manager
            self.last_processed = {}
        
        def on_modified(self, event):
            """
            Handle file modification events
            
            Args:
                event: File system event
            """
            if event.is_directory:
                return
            
            file_path = Path(event.src_path)
            
            # Check if it's a CSS or JS file (but not minified)
            if (file_path.suffix in ['.css', '.js'] and 
                not file_path.name.endswith('.min.css') and 
                not file_path.name.endswith('.min.js')):
                
                # Debounce rapid file changes
                now = time.time()
                if file_path in self.last_processed:
                    if now - self.last_processed[file_path] < 1.0:  # 1 second debounce
                        return
                
                self.last_processed[file_path] = now
                
                logger.info(f"Detected change in {file_path.name}, reprocessing...")
                
                # Process the changed file
                if file_path.suffix == '.css':
                    success, stats = self.asset_manager.minify_css_file(file_path)
                else:  # .js
                    success, stats = self.asset_manager.minify_js_file(file_path)
                
                if success:
                    logger.info(f"Successfully reprocessed {file_path.name}")
                else:
                    logger.error(f"Failed to reprocess {file_path.name}")

else:
    # Dummy class when watchdog is not available
    class AssetWatcher:
        def __init__(self, asset_manager):
            raise ImportError("watchdog package required for file watching functionality")


def start_watch_mode(asset_manager: AssetManager):
    """
    Start watch mode for automatic asset processing during development
    
    Args:
        asset_manager: AssetManager instance
    """
    if not WATCHDOG_AVAILABLE:
        logger.error("Watchdog not available - watch mode disabled")
        logger.info("Install watchdog: pip install watchdog")
        return
    
    logger.info("Starting asset watch mode...")
    logger.info("Watching for changes to CSS and JS files")
    logger.info("Press Ctrl+C to stop")
    
    event_handler = AssetWatcher(asset_manager)
    observer = Observer()
    
    # Watch CSS directory
    if asset_manager.css_dir.exists():
        observer.schedule(event_handler, str(asset_manager.css_dir), recursive=False)
        logger.info(f"Watching CSS directory: {asset_manager.css_dir}")
    
    # Watch JS directory
    if asset_manager.js_dir.exists():
        observer.schedule(event_handler, str(asset_manager.js_dir), recursive=False)
        logger.info(f"Watching JS directory: {asset_manager.js_dir}")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watch mode...")
        observer.stop()
    
    observer.join()
    logger.info("Watch mode stopped")


def main():
    """
    Main entry point for asset management
    
    Command line interface for asset minification and management
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Asset Manager for Site_proj')
    parser.add_argument('--watch', action='store_true', 
                       help='Watch for file changes and auto-minify (requires watchdog)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean all minified assets before processing')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize asset manager
    asset_manager = AssetManager()
    
    # Clean assets if requested
    if args.clean:
        asset_manager.clean_minified_assets()
    
    # Start watch mode or process assets once
    if args.watch:
        # Process assets once first
        stats = asset_manager.minify_all_assets()
        asset_manager.print_summary(stats)
        
        # Then start watching
        start_watch_mode(asset_manager)
    else:
        # Process assets and show summary
        stats = asset_manager.minify_all_assets()
        asset_manager.print_summary(stats)


if __name__ == "__main__":
    main()