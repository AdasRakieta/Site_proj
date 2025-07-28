# SmartHome iPhone App

This is an iOS application for connecting to and controlling the SmartHome PostgreSQL database.

## Features

- **Device Control**: Toggle lights, switches, and other smart devices
- **Temperature Control**: Monitor and adjust temperature settings
- **Security System**: View and control home security status
- **Room Management**: Navigate between different rooms
- **Real-time Updates**: Live synchronization with the database
- **User Authentication**: Secure login system

## Requirements

- iOS 14.0+
- Xcode 13+
- PostgreSQL database connection
- Swift 5.0+

## Installation

1. Open the project in Xcode
2. Configure database connection in `DatabaseConfig.swift`
3. Build and run on simulator or device

## Database Connection

The app connects to the same PostgreSQL database used by the Flask web application:
- Host: Configured in environment or DatabaseConfig.swift
- Database: admin
- Tables: users, rooms, devices, temperature_controls, automations, etc.

## Architecture

- **MVVM Pattern**: Clean separation of concerns
- **PostgreSQL Driver**: Direct database connectivity
- **SwiftUI**: Modern declarative UI framework
- **Combine**: Reactive programming for real-time updates

## Folder Structure

```
SmartHomeApp/
├── SmartHomeApp/
│   ├── Views/          # SwiftUI views
│   ├── Models/         # Data models
│   ├── Services/       # Database and network services
│   ├── ViewModels/     # MVVM view models
│   └── Utils/          # Utility classes
├── SmartHomeApp.xcodeproj
└── README.md
```