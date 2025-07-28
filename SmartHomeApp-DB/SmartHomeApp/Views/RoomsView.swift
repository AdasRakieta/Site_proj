//
//  RoomsView.swift
//  SmartHomeApp
//
//  Detailed rooms and devices view
//

import SwiftUI

struct RoomsView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var selectedRoom: Room?
    
    var body: some View {
        NavigationView {
            List {
                ForEach(databaseService.rooms) { room in
                    RoomDetailSection(room: room, devices: databaseService.getDevicesForRoom(room.id))
                }
            }
            .navigationTitle("Rooms")
            .refreshable {
                databaseService.loadRooms()
                databaseService.loadDevices()
            }
        }
    }
}

struct RoomDetailSection: View {
    let room: Room
    let devices: [Device]
    @EnvironmentObject var databaseService: DatabaseService
    @State private var isExpanded = true
    
    var body: some View {
        DisclosureGroup(isExpanded: $isExpanded) {
            if devices.isEmpty {
                Text("No devices in this room")
                    .foregroundColor(.secondary)
                    .italic()
                    .padding(.vertical, 8)
            } else {
                ForEach(devices) { device in
                    DeviceRow(device: device)
                }
            }
        } label: {
            RoomHeaderView(room: room, deviceCount: devices.count)
        }
        .padding(.vertical, 4)
    }
}

struct RoomHeaderView: View {
    let room: Room
    let deviceCount: Int
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(room.name)
                    .font(.headline)
                    .fontWeight(.semibold)
                
                if let description = room.description {
                    Text(description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("\(deviceCount)")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.blue)
                
                Text("devices")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 8)
    }
}

struct DeviceRow: View {
    let device: Device
    @EnvironmentObject var databaseService: DatabaseService
    
    var body: some View {
        HStack {
            // Device Icon
            Image(systemName: deviceIcon)
                .foregroundColor(deviceColor)
                .font(.title2)
                .frame(width: 30)
            
            // Device Info
            VStack(alignment: .leading, spacing: 2) {
                Text(device.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(device.type.rawValue.capitalized)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            // Device State Toggle
            Toggle("", isOn: Binding(
                get: { device.state == .on },
                set: { _ in
                    databaseService.toggleDevice(device)
                }
            ))
            .toggleStyle(SwitchToggleStyle(tint: .blue))
        }
        .padding(.vertical, 4)
        .opacity(device.state == .unavailable ? 0.5 : 1.0)
    }
    
    private var deviceIcon: String {
        switch device.type {
        case .light:
            return device.state == .on ? "lightbulb.fill" : "lightbulb"
        case .switch_:
            return "switch.2"
        case .sensor:
            return "sensor"
        case .thermostat:
            return "thermometer"
        case .camera:
            return "camera"
        case .speaker:
            return "speaker.wave.2"
        case .unknown:
            return "questionmark.circle"
        }
    }
    
    private var deviceColor: Color {
        switch device.state {
        case .on:
            return device.type == .light ? .yellow : .blue
        case .off:
            return .gray
        case .unavailable:
            return .red
        case .error:
            return .red
        }
    }
}

struct RoomsView_Previews: PreviewProvider {
    static var previews: some View {
        RoomsView()
            .environmentObject(DatabaseService())
    }
}