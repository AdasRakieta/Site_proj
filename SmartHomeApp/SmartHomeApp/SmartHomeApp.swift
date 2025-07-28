//
//  SmartHomeApp.swift
//  SmartHomeApp
//
//  Created for SmartHome PostgreSQL Database Integration
//

import SwiftUI

@main
struct SmartHomeApp: App {
    @StateObject private var databaseService = DatabaseService()
    @StateObject private var authViewModel = AuthenticationViewModel()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(databaseService)
                .environmentObject(authViewModel)
                .onAppear {
                    databaseService.initialize()
                }
        }
    }
}