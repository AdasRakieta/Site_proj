//
//  DashboardView.swift
//  SmartHomeApp
//
//  Main dashboard showing overview of smart home
//

import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @EnvironmentObject var authViewModel: AuthenticationViewModel
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    // Welcome Header
                    welcomeHeader
                    
                    // Quick Actions
                    quickActionsSection
                    
                    // Rooms Overview
                    roomsOverviewSection
                    
                    // Security Status
                    securityStatusSection
                    
                    // Temperature Overview
                    temperatureOverviewSection
                }
                .padding()
            }
            .navigationTitle("Dashboard")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Logout") {
                        authViewModel.logout()
                    }
                }
            }
        }
    }
    
    private var welcomeHeader: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                VStack(alignment: .leading) {
                    Text("Welcome back,")
                        .font(.title2)
                        .foregroundColor(.secondary)
                    
                    Text(authViewModel.currentUser?.name ?? "User")
                        .font(.title)
                        .fontWeight(.bold)
                }
                
                Spacer()
                
                VStack {
                    Circle()
                        .fill(databaseService.isConnected ? Color.green : Color.red)
                        .frame(width: 12, height: 12)
                    
                    Text(databaseService.isConnected ? "Connected" : "Offline")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color.blue.opacity(0.1))
        .cornerRadius(12)
    }
    
    private var quickActionsSection: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Quick Actions")
                .font(.headline)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 15) {
                QuickActionButton(
                    icon: "lightbulb.fill",
                    title: "All Lights",
                    action: { toggleAllLights() }
                )
                
                QuickActionButton(
                    icon: "shield.fill",
                    title: "Security",
                    action: { toggleSecurity() }
                )
                
                QuickActionButton(
                    icon: "thermometer",
                    title: "Temperature",
                    action: { /* Navigate to temperature */ }
                )
                
                QuickActionButton(
                    icon: "gear",
                    title: "Settings",
                    action: { /* Navigate to settings */ }
                )
            }
        }
    }
    
    private var roomsOverviewSection: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Rooms")
                .font(.headline)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 15) {
                ForEach(databaseService.rooms) { room in
                    RoomCard(room: room, devices: databaseService.getDevicesForRoom(room.id))
                }
            }
        }
    }
    
    private var securityStatusSection: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Security Status")
                .font(.headline)
                .fontWeight(.semibold)
            
            if let securityState = databaseService.securityState {
                SecurityStatusCard(securityState: securityState)
            }
        }
    }
    
    private var temperatureOverviewSection: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Temperature")
                .font(.headline)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 15) {
                ForEach(databaseService.temperatureControls) { control in
                    TemperatureCard(control: control)
                }
            }
        }
    }
    
    private func toggleAllLights() {
        let lightDevices = databaseService.devices.filter { $0.type == .light }
        for device in lightDevices {
            databaseService.toggleDevice(device)
        }
    }
    
    private func toggleSecurity() {
        if let currentState = databaseService.securityState {
            let newState: SecurityMode = currentState.state == .armed ? .disarmed : .armed
            databaseService.updateSecurityState(newState)
        }
    }
}

struct QuickActionButton: View {
    let icon: String
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(.blue)
                
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
            }
            .frame(maxWidth: .infinity, minHeight: 80)
            .background(Color.gray.opacity(0.1))
            .cornerRadius(12)
        }
    }
}

struct RoomCard: View {
    let room: Room
    let devices: [Device]
    
    var activeDevicesCount: Int {
        devices.filter { $0.state == .on }.count
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "house.fill")
                    .foregroundColor(.blue)
                
                Text(room.name)
                    .font(.headline)
                    .fontWeight(.medium)
                
                Spacer()
            }
            
            Text("\(activeDevicesCount)/\(devices.count) devices on")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct SecurityStatusCard: View {
    let securityState: SecurityState
    
    var body: some View {
        HStack {
            Image(systemName: securityState.state == .armed ? "shield.fill" : "shield")
                .foregroundColor(securityState.state == .armed ? .red : .green)
                .font(.title2)
            
            VStack(alignment: .leading) {
                Text(securityState.state.displayName)
                    .font(.headline)
                    .fontWeight(.medium)
                
                Text("Last changed: \(securityState.lastChanged, style: .time)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct TemperatureCard: View {
    let control: TemperatureControl
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "thermometer")
                    .foregroundColor(.orange)
                
                Text(control.name)
                    .font(.headline)
                    .fontWeight(.medium)
                
                Spacer()
            }
            
            Text("\(control.targetTemperature, specifier: "%.1f")°C")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.primary)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct DashboardView_Previews: PreviewProvider {
    static var previews: some View {
        DashboardView()
            .environmentObject(DatabaseService())
            .environmentObject(AuthenticationViewModel())
    }
}