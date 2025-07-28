"""
Apple SmartHome Routes
Handles the Apple/iOS optimized SmartHome interface
"""

from flask import Blueprint, render_template, send_from_directory, jsonify, request
import os

# Create Blueprint for Apple SmartHome
apple_bp = Blueprint('apple', __name__, 
                    url_prefix='/apple',
                    template_folder='templates',
                    static_folder='static')

# Add error handlers to the blueprint before registration
@apple_bp.errorhandler(404)
def apple_not_found(error):
    """Custom 404 handler for Apple app"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found.',
        'app': 'Apple SmartHome'
    }), 404

@apple_bp.errorhandler(500)
def apple_internal_error(error):
    """Custom 500 handler for Apple app"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal error occurred.',
        'app': 'Apple SmartHome'
    }), 500

class AppleSmartHomeRoutes:
    """Routes manager for Apple SmartHome application"""
    
    def __init__(self, app, smart_home=None, auth_manager=None):
        self.app = app
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.register_routes()
    
    def register_routes(self):
        """Register all Apple SmartHome routes"""
        
        @apple_bp.route('/')
        def index():
            """Main Apple SmartHome application page"""
            return render_template('apple.html')
        
        @apple_bp.route('/manifest.json')
        def manifest():
            """PWA manifest file"""
            return send_from_directory(
                os.path.join(apple_bp.static_folder),
                'manifest.json',
                mimetype='application/json'
            )
        
        @apple_bp.route('/sw.js')
        def service_worker():
            """Service Worker for PWA functionality"""
            return send_from_directory(
                os.path.join(apple_bp.static_folder, 'js'),
                'sw.js',
                mimetype='application/javascript'
            )
        
        @apple_bp.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files with proper caching headers"""
            response = send_from_directory(apple_bp.static_folder, filename)
            
            # Set caching headers for better performance
            if filename.endswith(('.css', '.js')):
                response.cache_control.max_age = 86400  # 1 day
            elif filename.endswith(('.png', '.jpg', '.jpeg', '.svg', '.ico')):
                response.cache_control.max_age = 604800  # 1 week
            
            return response
        
        @apple_bp.route('/status')
        def status():
            """Health check endpoint for the Apple app"""
            return jsonify({
                'status': 'ok',
                'app': 'Apple SmartHome',
                'version': '1.0.0',
                'authenticated': self.auth_manager.is_authenticated() if self.auth_manager else False
            })
        
        @apple_bp.route('/config')
        def config():
            """Configuration endpoint for the app"""
            if self.auth_manager and not self.auth_manager.is_authenticated():
                return jsonify({'error': 'Authentication required'}), 401
            
            config_data = {
                'app_name': 'Apple SmartHome',
                'version': '1.0.0',
                'features': {
                    'websocket': True,
                    'offline': True,
                    'notifications': True,
                    'haptic_feedback': True
                },
                'api_endpoints': {
                    'devices': '/api/buttons',
                    'temperature': '/api/temperature_controls',
                    'rooms': '/api/rooms',
                    'automations': '/api/automations'
                }
            }
            
            if self.smart_home:
                config_data['total_devices'] = len(self.smart_home.buttons) + len(self.smart_home.temperature_controls)
                config_data['total_rooms'] = len(self.smart_home.rooms)
                config_data['total_automations'] = len(self.smart_home.automations)
            
            return jsonify(config_data)


def register_apple_routes(app, smart_home=None, auth_manager=None):
    """Register Apple SmartHome routes with the Flask app"""
    
    # Create routes manager
    apple_routes = AppleSmartHomeRoutes(app, smart_home, auth_manager)
    
    # Register the blueprint
    app.register_blueprint(apple_bp)
    
    return apple_routes