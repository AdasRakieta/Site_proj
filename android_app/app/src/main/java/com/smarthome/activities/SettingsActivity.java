package com.smarthome.activities;

import android.os.Bundle;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.google.android.material.button.MaterialButton;
import com.smarthome.R;
import com.smarthome.services.ApiClient;

public class SettingsActivity extends AppCompatActivity {
    
    private EditText etServerUrl;
    private MaterialButton btnSave;
    private ApiClient apiClient;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);
        
        setTitle(getString(R.string.settings));
        
        initializeViews();
        apiClient = ApiClient.getInstance(this);
        loadCurrentSettings();
    }
    
    private void initializeViews() {
        etServerUrl = findViewById(R.id.etServerUrl);
        btnSave = findViewById(R.id.btnSave);
        
        btnSave.setOnClickListener(v -> saveSettings());
    }
    
    private void loadCurrentSettings() {
        etServerUrl.setText(apiClient.getServerUrl());
    }
    
    private void saveSettings() {
        String serverUrl = etServerUrl.getText().toString().trim();
        
        if (serverUrl.isEmpty()) {
            etServerUrl.setError("Wprowadź adres serwera");
            return;
        }
        
        // Ensure URL has protocol
        if (!serverUrl.startsWith("http://") && !serverUrl.startsWith("https://")) {
            serverUrl = "http://" + serverUrl;
        }
        
        // Ensure URL has port if not specified
        if (!serverUrl.contains(":") || serverUrl.endsWith("://")) {
            if (serverUrl.endsWith("/")) {
                serverUrl = serverUrl.substring(0, serverUrl.length() - 1);
            }
            serverUrl += ":5000";
        }
        
        apiClient.setServerUrl(serverUrl);
        Toast.makeText(this, "Ustawienia zapisane", Toast.LENGTH_SHORT).show();
        finish();
    }
}