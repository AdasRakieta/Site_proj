package com.smarthome.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import com.google.android.material.textfield.TextInputEditText;
import com.smarthome.R;
import com.smarthome.services.ApiClient;
import com.smarthome.services.SmartHomeApiService;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class LoginActivity extends AppCompatActivity {
    
    private TextInputEditText etUsername;
    private TextInputEditText etPassword;
    private Button btnLogin;
    private Button btnSettings;
    private ProgressBar progressBar;
    
    private ApiClient apiClient;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        
        initializeViews();
        apiClient = ApiClient.getInstance(this);
        setupClickListeners();
    }
    
    private void initializeViews() {
        etUsername = findViewById(R.id.etUsername);
        etPassword = findViewById(R.id.etPassword);
        btnLogin = findViewById(R.id.btnLogin);
        btnSettings = findViewById(R.id.btnSettings);
        progressBar = findViewById(R.id.progressBar);
    }
    
    private void setupClickListeners() {
        btnLogin.setOnClickListener(v -> attemptLogin());
        btnSettings.setOnClickListener(v -> showConnectionSettings());
    }
    
    private void attemptLogin() {
        String username = etUsername.getText().toString().trim();
        String password = etPassword.getText().toString().trim();
        
        if (username.isEmpty()) {
            etUsername.setError(getString(R.string.username));
            return;
        }
        
        if (password.isEmpty()) {
            etPassword.setError(getString(R.string.password));
            return;
        }
        
        setLoading(true);
        
        // Debug: Log current server URL
        android.util.Log.d("LoginActivity", "Current server URL: " + apiClient.getServerUrl());
        
        SmartHomeApiService.LoginRequest request = new SmartHomeApiService.LoginRequest(username, password);
        
        apiClient.getApiService().login(request).enqueue(new Callback<SmartHomeApiService.ApiResponse<SmartHomeApiService.LoginResponse>>() {
            @Override
            public void onResponse(Call<SmartHomeApiService.ApiResponse<SmartHomeApiService.LoginResponse>> call, 
                                 Response<SmartHomeApiService.ApiResponse<SmartHomeApiService.LoginResponse>> response) {
                setLoading(false);
                
                if (response.isSuccessful() && response.body() != null) {
                    SmartHomeApiService.ApiResponse<SmartHomeApiService.LoginResponse> apiResponse = response.body();
                    if (apiResponse.isSuccess()) {
                        // Login successful
                        Toast.makeText(LoginActivity.this, "Zalogowano pomyślnie", Toast.LENGTH_SHORT).show();
                        
                        // Navigate to main activity
                        Intent intent = new Intent(LoginActivity.this, MainActivity.class);
                        startActivity(intent);
                        finish();
                    } else {
                        Toast.makeText(LoginActivity.this, apiResponse.message != null ? apiResponse.message : getString(R.string.login_error), Toast.LENGTH_LONG).show();
                    }
                } else {
                    Toast.makeText(LoginActivity.this, getString(R.string.connection_error), Toast.LENGTH_LONG).show();
                }
            }
            
            @Override
            public void onFailure(Call<SmartHomeApiService.ApiResponse<SmartHomeApiService.LoginResponse>> call, Throwable t) {
                setLoading(false);
                Toast.makeText(LoginActivity.this, getString(R.string.connection_error) + ": " + t.getMessage(), Toast.LENGTH_LONG).show();
            }
        });
    }
    
    private void showConnectionSettings() {
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_connection_settings, null);
        EditText etServerUrl = dialogView.findViewById(R.id.etServerUrl);
        
        // Set current server URL
        etServerUrl.setText(apiClient.getServerUrl());
        
        new AlertDialog.Builder(this)
            .setTitle(getString(R.string.connection_settings))
            .setView(dialogView)
            .setPositiveButton(getString(R.string.save), (dialog, which) -> {
                String serverUrl = etServerUrl.getText().toString().trim();
                if (!serverUrl.isEmpty()) {
                    apiClient.setServerUrl(serverUrl);
                    Toast.makeText(this, "Ustawienia zapisane", Toast.LENGTH_SHORT).show();
                }
            })
            .setNegativeButton("Anuluj", null)
            .show();
    }
    
    private void setLoading(boolean loading) {
        progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        btnLogin.setEnabled(!loading);
        btnSettings.setEnabled(!loading);
        etUsername.setEnabled(!loading);
        etPassword.setEnabled(!loading);
    }
}