//
//  SecurityView.swift
//  SmartHomeApp
//
//  Security system control view
//

import SwiftUI

struct SecurityView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var showingConfirmation = false
    @State private var pendingSecurityState: SecurityMode?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 30) {
                if let securityState = databaseService.securityState {
                    // Security Status Display
                    SecurityStatusDisplay(securityState: securityState)
                    
                    // Security Control
                    SecurityControl(
                        currentState: securityState.state,
                        onStateChange: { newState in
                            pendingSecurityState = newState
                            showingConfirmation = true
                        }
                    )
                    
                    Spacer()
                    
                    // Security Log (mock data)
                    SecurityLog()
                    
                } else {
                    // Loading or error state
                    VStack(spacing: 20) {
                        ProgressView()
                            .scaleEffect(1.5)
                        
                        Text("Loading security status...")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .padding()
            .navigationTitle("Security")
            .alert("Change Security State", isPresent: $showingConfirmation) {
                Button("Cancel", role: .cancel) {
                    pendingSecurityState = nil
                }
                
                Button("Confirm") {
                    if let newState = pendingSecurityState {
                        databaseService.updateSecurityState(newState)
                    }
                    pendingSecurityState = nil
                }
            } message: {
                if let newState = pendingSecurityState {
                    Text("Are you sure you want to change security to \(newState.displayName)?")
                }
            }
        }
    }
}

struct SecurityStatusDisplay: View {
    let securityState: SecurityState
    
    var body: some View {
        VStack(spacing: 20) {
            // Status Icon
            ZStack {
                Circle()
                    .fill(statusColor.opacity(0.2))
                    .frame(width: 120, height: 120)
                
                Image(systemName: statusIcon)
                    .font(.system(size: 50))
                    .foregroundColor(statusColor)
            }
            
            // Status Text
            VStack(spacing: 8) {
                Text(securityState.state.displayName)
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(.primary)
                
                Text("Security System")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            // Last Changed Info
            VStack(spacing: 4) {
                Text("Last changed")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text(securityState.lastChanged, style: .relative)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                if let changedBy = securityState.changedBy {
                    Text("by \(changedBy)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(16)
    }
    
    private var statusColor: Color {
        switch securityState.state {
        case .armed:
            return .red
        case .disarmed:
            return .green
        }
    }
    
    private var statusIcon: String {
        switch securityState.state {
        case .armed:
            return "shield.fill"
        case .disarmed:
            return "shield"
        }
    }
}

struct SecurityControl: View {
    let currentState: SecurityMode
    let onStateChange: (SecurityMode) -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Security Control")
                .font(.headline)
                .fontWeight(.semibold)
            
            HStack(spacing: 20) {
                SecurityButton(
                    title: "Disarm",
                    icon: "shield",
                    color: .green,
                    isSelected: currentState == .disarmed,
                    action: { onStateChange(.disarmed) }
                )
                
                SecurityButton(
                    title: "Arm",
                    icon: "shield.fill",
                    color: .red,
                    isSelected: currentState == .armed,
                    action: { onStateChange(.armed) }
                )
            }
        }
    }
}

struct SecurityButton: View {
    let title: String
    let icon: String
    let color: Color
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.title)
                    .foregroundColor(isSelected ? .white : color)
                
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(isSelected ? .white : color)
            }
            .frame(maxWidth: .infinity, minHeight: 100)
            .background(isSelected ? color : color.opacity(0.1))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(color, lineWidth: isSelected ? 0 : 2)
            )
        }
        .disabled(isSelected)
    }
}

struct SecurityLog: View {
    @State private var logEntries: [SecurityLogEntry] = [
        SecurityLogEntry(
            id: "1",
            action: "System Armed",
            timestamp: Date().addingTimeInterval(-3600),
            user: "John Doe"
        ),
        SecurityLogEntry(
            id: "2",
            action: "System Disarmed",
            timestamp: Date().addingTimeInterval(-7200),
            user: "Jane Doe"
        ),
        SecurityLogEntry(
            id: "3",
            action: "System Armed",
            timestamp: Date().addingTimeInterval(-10800),
            user: "John Doe"
        )
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Recent Activity")
                .font(.headline)
                .fontWeight(.semibold)
            
            ScrollView {
                LazyVStack(spacing: 10) {
                    ForEach(logEntries) { entry in
                        SecurityLogRow(entry: entry)
                    }
                }
            }
            .frame(maxHeight: 200)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct SecurityLogRow: View {
    let entry: SecurityLogEntry
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(entry.action)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(entry.user)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Text(entry.timestamp, style: .time)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

struct SecurityLogEntry: Identifiable {
    let id: String
    let action: String
    let timestamp: Date
    let user: String
}

struct SecurityView_Previews: PreviewProvider {
    static var previews: some View {
        SecurityView()
            .environmentObject(DatabaseService())
    }
}