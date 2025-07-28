# SmartHome iPhone App - Installation Guide

## Prerequisites

- **macOS** with Xcode 14.0 or later
- **iOS 14.0+** device or simulator
- **PostgreSQL database** (same as used by the Flask web application)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/AdasRakieta/Site_proj.git
cd Site_proj/SmartHomeApp
```

### 2. Open in Xcode

```bash
open SmartHomeApp.xcodeproj
```

### 3. Configure Database Connection

1. Open `SmartHomeApp/Utils/DatabaseConfig.swift`
2. Update the database connection parameters if needed:

```swift
static let host = "your-database-host"
static let port = 5432
static let database = "your-database-name"
static let username = "your-username"  
static let password = "your-password"
```

Alternatively, set environment variables:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### 4. Install Dependencies

The app uses Swift Package Manager for dependencies. Xcode will automatically resolve them when you build.

### 5. Build and Run

1. Select your target device or simulator
2. Press **Cmd+R** to build and run
3. The app will launch with a login screen

## Demo Credentials

For testing purposes, use these credentials:
- **Email**: admin@smarthome.com
- **Password**: admin123

## Features

### Dashboard
- Overview of all smart home systems
- Quick access to common controls
- Real-time status indicators

### Rooms
- Browse all rooms in your home
- Control individual devices
- Toggle lights and switches

### Temperature
- Monitor room temperatures
- Adjust thermostat settings
- View temperature history

### Security
- Arm/disarm security system
- View security status
- Security activity log

### Settings
- User profile management
- Database connection status
- App information

## Database Schema

The app connects to the same PostgreSQL database used by the Flask web application. Required tables:

- `users` - User authentication
- `rooms` - Room information
- `devices` - Smart home devices
- `temperature_controls` - Thermostat controls
- `automations` - Automated rules
- `security_state` - Security system status

## Troubleshooting

### Database Connection Issues

1. Verify database credentials in `DatabaseConfig.swift`
2. Ensure PostgreSQL server is running and accessible
3. Check network connectivity from iOS device
4. Review database permissions

### Build Errors

1. Clean build folder: **Product → Clean Build Folder**
2. Reset package cache: **File → Packages → Reset Package Caches**
3. Update Xcode to latest version
4. Verify iOS deployment target (14.0+)

### Runtime Issues

1. Check device logs in Xcode console
2. Verify database schema matches expected structure
3. Test database connection from other tools
4. Review network permissions in Info.plist

## Development

### Adding New Features

1. Create new SwiftUI views in `Views/` folder
2. Add data models in `Models/` folder
3. Implement services in `Services/` folder
4. Update navigation in `ContentView.swift`

### Database Integration

The app uses a simulated database service for demonstration. To connect to a real PostgreSQL database:

1. Add PostgresNIO dependency
2. Update `DatabaseService.swift` with real connection logic
3. Implement proper error handling
4. Add connection pooling for better performance

## Support

For issues and questions:

1. Check the Flask web application logs
2. Review PostgreSQL database logs
3. Verify network connectivity
4. Test with database administration tools

## Security Notes

- Store database credentials securely
- Use environment variables for sensitive data
- Enable SSL/TLS for database connections
- Implement proper user authentication
- Regular security updates

## Future Enhancements

- Real-time push notifications
- Biometric authentication
- Offline mode support
- Widget support
- Apple Watch companion app
- Siri integration