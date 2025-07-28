# Apple SmartHome App

A Progressive Web App (PWA) optimized for iPhone and iPad devices to control the SmartHome system via VPN.

## Features

- **iOS Optimized**: Native-like experience on iPhone/iPad
- **Offline Capable**: Service Worker for offline functionality
- **Touch Gestures**: Optimized for touch interactions
- **Homescreen Installation**: Can be added to iOS homescreen
- **Real-time Updates**: WebSocket integration for live device status
- **VPN Compatible**: Works seamlessly over VPN connections

## Architecture

- **Frontend**: Vanilla JavaScript ES6+ with modern Web APIs
- **Styling**: CSS3 with iOS-specific optimizations
- **Communication**: REST API + WebSocket for real-time updates
- **Offline**: Service Worker for caching and offline functionality
- **Icons**: Apple Touch Icons for homescreen installation

## Installation on iPhone

1. Open Safari and navigate to the SmartHome URL via VPN
2. Tap the Share button
3. Select "Add to Home Screen"
4. The app will appear as a native-looking icon on your homescreen

## Technical Details

- Uses existing SmartHome API endpoints
- Mobile-first responsive design
- iOS Safari optimizations
- Touch-friendly interface elements
- Haptic feedback integration (where supported)