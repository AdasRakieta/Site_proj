//
//  LoginView.swift
//  SmartHomeApp
//
//  User authentication view
//

import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authViewModel: AuthenticationViewModel
    @State private var email = ""
    @State private var password = ""
    @State private var showPassword = false
    
    var body: some View {
        VStack(spacing: 30) {
            // App Logo and Title
            VStack(spacing: 20) {
                Image(systemName: "house.fill")
                    .font(.system(size: 80))
                    .foregroundColor(.blue)
                
                Text("SmartHome")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .foregroundColor(.primary)
                
                Text("Control your home from anywhere")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .padding(.bottom, 40)
            
            // Login Form
            VStack(spacing: 20) {
                // Email Field
                VStack(alignment: .leading, spacing: 5) {
                    Text("Email")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    TextField("Enter your email", text: $email)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                }
                
                // Password Field
                VStack(alignment: .leading, spacing: 5) {
                    Text("Password")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    HStack {
                        if showPassword {
                            TextField("Enter your password", text: $password)
                        } else {
                            SecureField("Enter your password", text: $password)
                        }
                        
                        Button(action: { showPassword.toggle() }) {
                            Image(systemName: showPassword ? "eye.slash" : "eye")
                                .foregroundColor(.secondary)
                        }
                    }
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .textContentType(.password)
                }
                
                // Error Message
                if let errorMessage = authViewModel.errorMessage {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .font(.caption)
                        .multilineTextAlignment(.center)
                }
                
                // Login Button
                Button(action: {
                    authViewModel.login(email: email, password: password)
                }) {
                    HStack {
                        if authViewModel.isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .scaleEffect(0.8)
                        }
                        
                        Text("Login")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(authViewModel.isLoading || email.isEmpty || password.isEmpty)
                
                // Demo Credentials Info
                VStack(spacing: 5) {
                    Text("Demo Credentials:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("Email: admin@smarthome.com")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("Password: admin123")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 20)
            }
            .padding(.horizontal, 40)
            
            Spacer()
        }
        .padding()
        .navigationBarHidden(true)
    }
}

struct LoginView_Previews: PreviewProvider {
    static var previews: some View {
        LoginView()
            .environmentObject(AuthenticationViewModel())
    }
}