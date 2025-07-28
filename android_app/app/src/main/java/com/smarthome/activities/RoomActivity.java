package com.smarthome.activities;

import android.os.Bundle;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.smarthome.R;
import com.smarthome.models.Device;
import com.smarthome.services.ApiClient;
import com.smarthome.utils.DeviceAdapter;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class RoomActivity extends AppCompatActivity {
    
    private RecyclerView rvDevices;
    private DeviceAdapter deviceAdapter;
    private List<Device> devices = new ArrayList<>();
    private ApiClient apiClient;
    private String roomName;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_room);
        
        roomName = getIntent().getStringExtra("room_name");
        if (roomName != null) {
            setTitle(roomName);
        }
        
        initializeViews();
        apiClient = ApiClient.getInstance(this);
        loadDevicesForRoom();
    }
    
    private void initializeViews() {
        rvDevices = findViewById(R.id.rvDevices);
        
        deviceAdapter = new DeviceAdapter(devices, device -> {
            toggleDevice(device);
        });
        rvDevices.setLayoutManager(new LinearLayoutManager(this));
        rvDevices.setAdapter(deviceAdapter);
    }
    
    private void loadDevicesForRoom() {
        apiClient.getApiService().getDevices().enqueue(new Callback<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Device>>>() {
            @Override
            public void onResponse(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Device>>> call, 
                                 Response<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Device>>> response) {
                if (response.isSuccessful() && response.body() != null && response.body().isSuccess()) {
                    devices.clear();
                    if (response.body().data != null) {
                        // Filter devices for this room
                        for (Device device : response.body().data) {
                            if (roomName != null && roomName.equals(device.getRoom())) {
                                devices.add(device);
                            }
                        }
                    }
                    deviceAdapter.notifyDataSetChanged();
                }
            }
            
            @Override
            public void onFailure(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Device>>> call, Throwable t) {
                Toast.makeText(RoomActivity.this, "Błąd ładowania urządzeń: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void toggleDevice(Device device) {
        apiClient.getApiService().toggleDevice(device.getId()).enqueue(new Callback<com.smarthome.services.SmartHomeApiService.ApiResponse<String>>() {
            @Override
            public void onResponse(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<String>> call, 
                                 Response<com.smarthome.services.SmartHomeApiService.ApiResponse<String>> response) {
                if (response.isSuccessful() && response.body() != null && response.body().isSuccess()) {
                    device.setState(!device.isState());
                    deviceAdapter.notifyDataSetChanged();
                    Toast.makeText(RoomActivity.this, "Urządzenie przełączone", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(RoomActivity.this, "Błąd przełączania urządzenia", Toast.LENGTH_SHORT).show();
                }
            }
            
            @Override
            public void onFailure(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<String>> call, Throwable t) {
                Toast.makeText(RoomActivity.this, "Błąd połączenia: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}