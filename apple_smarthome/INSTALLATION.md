# Apple SmartHome - Installation Guide

## Overview
Apple SmartHome is a Progressive Web App (PWA) optimized for iPhone and iPad devices. It provides a native-like experience for controlling your SmartHome system via VPN connection.

## Features
- **iOS Optimized Interface**: Native-like appearance and behavior on iOS devices
- **Progressive Web App**: Can be installed to home screen like a native app
- **Offline Capability**: Works offline with cached data using Service Worker
- **Real-time Updates**: WebSocket integration for live device status updates
- **Touch Optimized**: Haptic feedback and touch-friendly controls
- **VPN Compatible**: Works seamlessly over VPN connections
- **Mobile First**: Responsive design optimized for mobile screens

## Installation

### Prerequisites
- SmartHome application running and accessible
- iPhone or iPad with Safari browser
- VPN connection configured (if accessing remotely)

### Steps

1. **Access the Application**
   - Open Safari on your iPhone/iPad
   - Navigate to your SmartHome server: `https://your-server-address/apple/`
   - Or via VPN: `http://your-vpn-address/apple/`

2. **Install to Home Screen**
   - Tap the Share button (square with arrow) in Safari
   - Scroll down and tap "Add to Home Screen"
   - Customize the name if desired (default: "SmartHome")
   - Tap "Add"

3. **Launch the App**
   - Find the SmartHome icon on your home screen
   - Tap to launch the app
   - The app will open in full-screen mode like a native app

## Usage

### Login
- Enter your SmartHome username and password
- The app will remember your login (unless you log out)

### Device Control
- **Lights**: Tap device cards to toggle lights on/off
- **Temperature**: Use +/- buttons to adjust temperature
- **Real-time Updates**: Changes appear instantly across all connected devices

### Navigation
- **Devices Tab**: Control lights and temperature
- **Rooms Tab**: View devices organized by room
- **Automations Tab**: Toggle automation rules

### Offline Mode
- The app caches device states for offline access
- Changes made offline will sync when connection returns
- Status indicator shows connection state

## Technical Details

### PWA Features
- Service Worker for offline functionality
- Web App Manifest for native installation
- Apple Touch Icons for home screen
- iOS Safari optimizations

### Compatibility
- iOS 12.0+ (Safari)
- iPadOS 13.0+
- Modern browsers with PWA support

### Performance
- Optimized assets and caching
- Minimal network usage
- Fast startup times
- Smooth animations

## VPN Setup
The Apple app works seamlessly with your existing VPN configuration:

1. **Raspberry Pi VPN**: If your SmartHome runs on Raspberry Pi with VPN
2. **Port Forwarding**: Ensure port 5000-5001 is accessible
3. **HTTPS**: Recommended for production use
4. **Network Access**: App uses same endpoints as web interface

## Troubleshooting

### Can't Install to Home Screen
- Ensure you're using Safari (not Chrome or other browsers)
- Check that the site is served over HTTPS (for production)
- Try refreshing the page and retry

### Login Issues
- Verify your credentials work on the main web interface
- Check VPN connection
- Clear Safari cache and cookies

### Offline Issues
- Ensure the app was fully loaded before going offline
- Check that Service Worker is enabled in Safari settings
- Reload the app when back online

### Performance Issues
- Close other Safari tabs
- Restart Safari
- Reboot device if needed

## Advanced Configuration

### Customization
- App icons and splash screens can be customized
- Colors and themes can be modified in CSS
- Additional features can be added via JavaScript

### Development
```bash
# Test the application locally
cd Site_proj
python test_apple_app.py

# Generate new icons
cd apple_smarthome
python generate_icons.py
```

### Updates
- The app automatically checks for updates
- Service Worker caches are updated automatically
- Force refresh: delete app and reinstall from Safari

## Support
For issues specific to the Apple SmartHome app:
1. Check the main SmartHome application is running
2. Verify VPN/network connectivity
3. Test the web interface at `/apple/` in Safari
4. Check browser console for JavaScript errors

---

**Note**: This Apple SmartHome PWA is designed to work alongside your existing VPN setup with Raspberry Pi. It provides a mobile-optimized interface while maintaining all the security and functionality of the main SmartHome system.