//
//  DatabaseConfig.swift
//  SmartHomeApp
//
//  Database connection configuration
//

import Foundation

struct DatabaseConfig {
    // Database connection parameters - matches the Flask app configuration
    static let host = ProcessInfo.processInfo.environment["DB_HOST"] ?? "100.103.184.90"
    static let port = Int(ProcessInfo.processInfo.environment["DB_PORT"] ?? "5432") ?? 5432
    static let database = ProcessInfo.processInfo.environment["DB_NAME"] ?? "admin"
    static let username = ProcessInfo.processInfo.environment["DB_USER"] ?? "admin"
    static let password = ProcessInfo.processInfo.environment["DB_PASSWORD"] ?? "Qwuizzy123."
    
    // Connection string for PostgreSQL
    static var connectionString: String {
        return "host=\(host) port=\(port) dbname=\(database) user=\(username) password=\(password) connect_timeout=5"
    }
    
    // Default home ID - matches the Flask app
    static let homeId = ProcessInfo.processInfo.environment["HOME_ID"] ?? "default-home"
}