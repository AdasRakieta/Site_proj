//
//  AuthenticationViewModel.swift
//  SmartHomeApp
//
//  Authentication view model for user login
//

import Foundation
import Combine

class AuthenticationViewModel: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var errorMessage: String?
    @Published var isLoading = false
    
    private let userDefaults = UserDefaults.standard
    private let authKey = "smartHomeAuthUser"
    
    init() {
        checkSavedAuthentication()
    }
    
    private func checkSavedAuthentication() {
        // Check if user is already logged in
        if let userData = userDefaults.data(forKey: authKey),
           let user = try? JSONDecoder().decode(User.self, from: userData) {
            DispatchQueue.main.async {
                self.currentUser = user
                self.isAuthenticated = true
            }
        }
    }
    
    func login(email: String, password: String) {
        guard !email.isEmpty && !password.isEmpty else {
            errorMessage = "Please enter both email and password"
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        // Simulate authentication (in real app, connect to database)
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.performLogin(email: email, password: password)
        }
    }
    
    private func performLogin(email: String, password: String) {
        // For demonstration, accept demo credentials
        if email.lowercased() == "admin@smarthome.com" && password == "admin123" {
            let user = User(
                id: "user-1",
                name: "Administrator",
                email: email,
                passwordHash: "hashed_password",
                isAdmin: true,
                isActive: true,
                createdAt: Date(),
                lastLogin: Date()
            )
            
            saveUser(user)
            
            DispatchQueue.main.async {
                self.currentUser = user
                self.isAuthenticated = true
                self.isLoading = false
                self.errorMessage = nil
            }
        } else {
            DispatchQueue.main.async {
                self.errorMessage = "Invalid email or password"
                self.isLoading = false
            }
        }
    }
    
    private func saveUser(_ user: User) {
        if let userData = try? JSONEncoder().encode(user) {
            userDefaults.set(userData, forKey: authKey)
        }
    }
    
    func logout() {
        userDefaults.removeObject(forKey: authKey)
        
        DispatchQueue.main.async {
            self.currentUser = nil
            self.isAuthenticated = false
            self.errorMessage = nil
        }
    }
}