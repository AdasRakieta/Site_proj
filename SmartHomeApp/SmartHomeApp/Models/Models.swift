//
//  Models.swift
//  SmartHomeApp
//
//  Data models matching PostgreSQL database schema
//

import Foundation

// MARK: - User Model
struct User: Codable, Identifiable {
    let id: String
    let name: String
    let email: String
    let passwordHash: String
    let isAdmin: Bool
    let isActive: Bool
    let createdAt: Date
    let lastLogin: Date?
    
    enum CodingKeys: String, CodingKey {
        case id = "user_id"
        case name
        case email
        case passwordHash = "password_hash"
        case isAdmin = "is_admin"
        case isActive = "is_active"
        case createdAt = "created_at"
        case lastLogin = "last_login"
    }
}

// MARK: - Room Model
struct Room: Codable, Identifiable {
    let id: String
    let homeId: String
    let name: String
    let description: String?
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id = "room_id"
        case homeId = "home_id"
        case name
        case description
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - Device Model
struct Device: Codable, Identifiable {
    let id: String
    let roomId: String
    let name: String
    let type: DeviceType
    let state: DeviceState
    let properties: [String: Any]?
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id = "device_id"
        case roomId = "room_id"
        case name
        case type
        case state
        case properties
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
    
    // Custom decoding for properties
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        roomId = try container.decode(String.self, forKey: .roomId)
        name = try container.decode(String.self, forKey: .name)
        type = try container.decode(DeviceType.self, forKey: .type)
        state = try container.decode(DeviceState.self, forKey: .state)
        createdAt = try container.decode(Date.self, forKey: .createdAt)
        updatedAt = try container.decode(Date.self, forKey: .updatedAt)
        
        // Handle properties as JSON
        if let propertiesData = try? container.decode(Data.self, forKey: .properties) {
            properties = try? JSONSerialization.jsonObject(with: propertiesData) as? [String: Any]
        } else {
            properties = nil
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(roomId, forKey: .roomId)
        try container.encode(name, forKey: .name)
        try container.encode(type, forKey: .type)
        try container.encode(state, forKey: .state)
        try container.encode(createdAt, forKey: .createdAt)
        try container.encode(updatedAt, forKey: .updatedAt)
        
        if let properties = properties {
            let propertiesData = try JSONSerialization.data(withJSONObject: properties)
            try container.encode(propertiesData, forKey: .properties)
        }
    }
}

// MARK: - Device Type Enum
enum DeviceType: String, Codable, CaseIterable {
    case light = "light"
    case switch_ = "switch"
    case sensor = "sensor"
    case thermostat = "thermostat"
    case camera = "camera"
    case speaker = "speaker"
    case unknown = "unknown"
}

// MARK: - Device State Enum
enum DeviceState: String, Codable, CaseIterable {
    case on = "on"
    case off = "off"
    case unavailable = "unavailable"
    case error = "error"
}

// MARK: - Temperature Control Model
struct TemperatureControl: Codable, Identifiable {
    let id: String
    let roomId: String
    let name: String
    let currentTemperature: Double
    let targetTemperature: Double
    let minTemperature: Double
    let maxTemperature: Double
    let isActive: Bool
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id = "control_id"
        case roomId = "room_id"
        case name
        case currentTemperature = "current_temperature"
        case targetTemperature = "target_temperature"
        case minTemperature = "min_temperature"
        case maxTemperature = "max_temperature"
        case isActive = "is_active"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - Automation Model
struct Automation: Codable, Identifiable {
    let id: String
    let homeId: String
    let name: String
    let description: String?
    let isActive: Bool
    let trigger: AutomationTrigger
    let actions: [AutomationAction]
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id = "automation_id"
        case homeId = "home_id"
        case name
        case description
        case isActive = "is_active"
        case trigger
        case actions
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct AutomationTrigger: Codable {
    let type: String
    let conditions: [String: Any]
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        type = try container.decode(String.self, forKey: .type)
        
        if let conditionsData = try? container.decode(Data.self, forKey: .conditions) {
            conditions = try JSONSerialization.jsonObject(with: conditionsData) as? [String: Any] ?? [:]
        } else {
            conditions = [:]
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(type, forKey: .type)
        let conditionsData = try JSONSerialization.data(withJSONObject: conditions)
        try container.encode(conditionsData, forKey: .conditions)
    }
    
    enum CodingKeys: String, CodingKey {
        case type, conditions
    }
}

struct AutomationAction: Codable {
    let type: String
    let parameters: [String: Any]
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        type = try container.decode(String.self, forKey: .type)
        
        if let parametersData = try? container.decode(Data.self, forKey: .parameters) {
            parameters = try JSONSerialization.jsonObject(with: parametersData) as? [String: Any] ?? [:]
        } else {
            parameters = [:]
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(type, forKey: .type)
        let parametersData = try JSONSerialization.data(withJSONObject: parameters)
        try container.encode(parametersData, forKey: .parameters)
    }
    
    enum CodingKeys: String, CodingKey {
        case type, parameters
    }
}

// MARK: - Security State Model
struct SecurityState: Codable {
    let homeId: String
    let state: SecurityMode
    let lastChanged: Date
    let changedBy: String?
    
    enum CodingKeys: String, CodingKey {
        case homeId = "home_id"
        case state
        case lastChanged = "last_changed"
        case changedBy = "changed_by"
    }
}

enum SecurityMode: String, Codable, CaseIterable {
    case armed = "Załączony"
    case disarmed = "Wyłączony"
    
    var displayName: String {
        switch self {
        case .armed: return "Armed"
        case .disarmed: return "Disarmed"
        }
    }
}