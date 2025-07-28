//
//  ContentView.swift
//  SmartHomeApp
//
//  Main content view with navigation
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authViewModel: AuthenticationViewModel
    @EnvironmentObject var databaseService: DatabaseService
    
    var body: some View {
        NavigationView {
            if authViewModel.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
}

struct MainTabView: View {
    var body: some View {
        TabView {
            DashboardView()
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("Home")
                }
            
            RoomsView()
                .tabItem {
                    Image(systemName: "rectangle.grid.2x2")
                    Text("Rooms")
                }
            
            TemperatureView()
                .tabItem {
                    Image(systemName: "thermometer")
                    Text("Temperature")
                }
            
            SecurityView()
                .tabItem {
                    Image(systemName: "shield.fill")
                    Text("Security")
                }
            
            SettingsView()
                .tabItem {
                    Image(systemName: "gear")
                    Text("Settings")
                }
        }
        .accentColor(.blue)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .environmentObject(AuthenticationViewModel())
            .environmentObject(DatabaseService())
    }
}