//
//  TemperatureView.swift
//  SmartHomeApp
//
//  Temperature control view for all rooms
//

import SwiftUI

struct TemperatureView: View {
    @EnvironmentObject var databaseService: DatabaseService
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    ForEach(databaseService.temperatureControls) { control in
                        TemperatureControlCard(control: control)
                    }
                    
                    if databaseService.temperatureControls.isEmpty {
                        EmptyStateView(
                            icon: "thermometer",
                            title: "No Temperature Controls",
                            message: "No temperature controls are configured for your home."
                        )
                    }
                }
                .padding()
            }
            .navigationTitle("Temperature")
            .refreshable {
                databaseService.loadTemperatureControls()
            }
        }
    }
}

struct TemperatureControlCard: View {
    let control: TemperatureControl
    @EnvironmentObject var databaseService: DatabaseService
    @State private var targetTemperature: Double
    @State private var isEditing = false
    
    init(control: TemperatureControl) {
        self.control = control
        self._targetTemperature = State(initialValue: control.targetTemperature)
    }
    
    var body: some View {
        VStack(spacing: 20) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(control.name)
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    Text(databaseService.getRoomName(control.roomId))
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Button(action: { isEditing.toggle() }) {
                    Image(systemName: isEditing ? "checkmark.circle.fill" : "pencil.circle")
                        .foregroundColor(.blue)
                        .font(.title2)
                }
            }
            
            // Temperature Display
            HStack(spacing: 30) {
                // Current Temperature
                VStack(spacing: 8) {
                    Text("Current")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("\(control.currentTemperature, specifier: "%.1f")°")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundColor(.primary)
                }
                
                // Target Temperature
                VStack(spacing: 8) {
                    Text("Target")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    if isEditing {
                        Text("\(targetTemperature, specifier: "%.1f")°")
                            .font(.title)
                            .fontWeight(.bold)
                            .foregroundColor(.blue)
                    } else {
                        Text("\(control.targetTemperature, specifier: "%.1f")°")
                            .font(.title)
                            .fontWeight(.bold)
                            .foregroundColor(.blue)
                    }
                }
            }
            
            // Temperature Slider (when editing)
            if isEditing {
                VStack(spacing: 10) {
                    Slider(
                        value: $targetTemperature,
                        in: control.minTemperature...control.maxTemperature,
                        step: 0.5
                    ) {
                        Text("Temperature")
                    } minimumValueLabel: {
                        Text("\(control.minTemperature, specifier: "%.0f")°")
                            .font(.caption)
                    } maximumValueLabel: {
                        Text("\(control.maxTemperature, specifier: "%.0f")°")
                            .font(.caption)
                    }
                    .accentColor(.blue)
                    
                    HStack {
                        Button("Cancel") {
                            targetTemperature = control.targetTemperature
                            isEditing = false
                        }
                        .foregroundColor(.secondary)
                        
                        Spacer()
                        
                        Button("Save") {
                            databaseService.updateTemperature(control.id, temperature: targetTemperature)
                            isEditing = false
                        }
                        .fontWeight(.semibold)
                        .foregroundColor(.blue)
                    }
                    .font(.subheadline)
                }
            }
            
            // Status Indicator
            HStack {
                Circle()
                    .fill(control.isActive ? Color.green : Color.red)
                    .frame(width: 8, height: 8)
                
                Text(control.isActive ? "Active" : "Inactive")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text("Updated: \(control.updatedAt, style: .time)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
        .onChange(of: control.targetTemperature) { newValue in
            if !isEditing {
                targetTemperature = newValue
            }
        }
    }
}

struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: icon)
                .font(.system(size: 60))
                .foregroundColor(.gray)
            
            Text(title)
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.primary)
            
            Text(message)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding()
    }
}

struct TemperatureView_Previews: PreviewProvider {
    static var previews: some View {
        TemperatureView()
            .environmentObject(DatabaseService())
    }
}