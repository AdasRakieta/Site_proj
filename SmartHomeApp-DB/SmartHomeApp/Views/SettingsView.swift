//
//  SettingsView.swift
//  SmartHomeApp
//
//  App settings and configuration view
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var authViewModel: AuthenticationViewModel
    @EnvironmentObject var databaseService: DatabaseService
    @State private var showingLogoutAlert = false
    
    var body: some View {
        NavigationView {
            List {
                // User Section
                Section("User") {
                    UserProfileRow()
                    
                    Button("Logout") {
                        showingLogoutAlert = true
                    }
                    .foregroundColor(.red)
                }
                
                // Database Section
                Section("Database") {
                    DatabaseConnectionRow()
                    
                    Button("Refresh Data") {
                        databaseService.loadInitialData()
                    }
                    .foregroundColor(.blue)
                }
                
                // App Information
                Section("App Information") {
                    InfoRow(title: "Version", value: "1.0.0")
                    InfoRow(title: "Build", value: "1")
                    InfoRow(title: "Database Host", value: DatabaseConfig.host)
                    InfoRow(title: "Database Name", value: DatabaseConfig.database)
                }
                
                // Support Section
                Section("Support") {
                    NavigationLink("Help & Support") {
                        HelpView()
                    }
                    
                    NavigationLink("About") {
                        AboutView()
                    }
                }
            }
            .navigationTitle("Settings")
            .alert("Logout", isPresented: $showingLogoutAlert) {
                Button("Cancel", role: .cancel) { }
                Button("Logout", role: .destructive) {
                    authViewModel.logout()
                }
            } message: {
                Text("Are you sure you want to logout?")
            }
        }
    }
}

struct UserProfileRow: View {
    @EnvironmentObject var authViewModel: AuthenticationViewModel
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(authViewModel.currentUser?.name ?? "Unknown User")
                    .font(.headline)
                    .fontWeight(.medium)
                
                Text(authViewModel.currentUser?.email ?? "No email")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            if authViewModel.currentUser?.isAdmin == true {
                Text("Admin")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.blue.opacity(0.2))
                    .foregroundColor(.blue)
                    .cornerRadius(4)
            }
        }
        .padding(.vertical, 4)
    }
}

struct DatabaseConnectionRow: View {
    @EnvironmentObject var databaseService: DatabaseService
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Database Connection")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text("\(DatabaseConfig.host):\(DatabaseConfig.port)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            HStack(spacing: 8) {
                Circle()
                    .fill(databaseService.isConnected ? Color.green : Color.red)
                    .frame(width: 8, height: 8)
                
                Text(databaseService.isConnected ? "Connected" : "Disconnected")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct InfoRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .font(.subheadline)
            
            Spacer()
            
            Text(value)
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }
}

struct HelpView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("How to Use SmartHome App")
                    .font(.title)
                    .fontWeight(.bold)
                
                HelpSection(
                    title: "Dashboard",
                    content: "The dashboard provides an overview of your smart home. You can see quick actions, room status, security state, and temperature controls."
                )
                
                HelpSection(
                    title: "Rooms",
                    content: "Browse through all your rooms and control individual devices. Toggle lights and switches directly from the room view."
                )
                
                HelpSection(
                    title: "Temperature",
                    content: "Monitor and adjust temperature controls for different rooms. Tap the edit button to change target temperatures."
                )
                
                HelpSection(
                    title: "Security",
                    content: "Control your home security system. Arm or disarm the system and view recent security activity."
                )
                
                HelpSection(
                    title: "Database Connection",
                    content: "The app connects to your PostgreSQL database to sync smart home data. Check the connection status in Settings."
                )
            }
            .padding()
        }
        .navigationTitle("Help")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct HelpSection: View {
    let title: String
    let content: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.headline)
                .fontWeight(.semibold)
            
            Text(content)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

struct AboutView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: 30) {
                // App Icon and Name
                VStack(spacing: 15) {
                    Image(systemName: "house.fill")
                        .font(.system(size: 80))
                        .foregroundColor(.blue)
                    
                    Text("SmartHome")
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text("Version 1.0.0")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                // Description
                VStack(alignment: .leading, spacing: 15) {
                    Text("About SmartHome")
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    Text("SmartHome is an iOS application designed to connect to and control your smart home devices through a PostgreSQL database. Built with SwiftUI and modern iOS technologies.")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                
                // Features
                VStack(alignment: .leading, spacing: 15) {
                    Text("Features")
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        FeatureRow(icon: "lightbulb.fill", text: "Device Control")
                        FeatureRow(icon: "thermometer", text: "Temperature Management")
                        FeatureRow(icon: "shield.fill", text: "Security System")
                        FeatureRow(icon: "house.fill", text: "Room Organization")
                        FeatureRow(icon: "arrow.clockwise", text: "Real-time Sync")
                    }
                }
                
                Spacer()
                
                // Copyright
                Text("© 2024 SmartHome App. All rights reserved.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding()
        }
        .navigationTitle("About")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct FeatureRow: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.blue)
                .frame(width: 20)
            
            Text(text)
                .font(.subheadline)
        }
    }
}

struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SettingsView()
            .environmentObject(AuthenticationViewModel())
            .environmentObject(DatabaseService())
    }
}