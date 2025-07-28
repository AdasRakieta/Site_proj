package com.smarthome.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.MenuItem;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.ActionBarDrawerToggle;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.GravityCompat;
import androidx.drawerlayout.widget.DrawerLayout;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import com.google.android.material.appbar.MaterialToolbar;
import com.google.android.material.navigation.NavigationView;
import com.smarthome.R;
import com.smarthome.models.Device;
import com.smarthome.models.Room;
import com.smarthome.models.SecurityStateResponse;
import com.smarthome.services.ApiClient;
import com.smarthome.utils.DeviceAdapter;
import com.smarthome.utils.RoomAdapter;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MainActivity extends AppCompatActivity implements NavigationView.OnNavigationItemSelectedListener {
    
    private DrawerLayout drawerLayout;
    private NavigationView navigationView;
    private MaterialToolbar toolbar;
    private SwipeRefreshLayout swipeRefresh;
    private TextView tvSecurityStatus;
    private RecyclerView rvRooms;
    private RecyclerView rvQuickControls;
    
    private RoomAdapter roomAdapter;
    private DeviceAdapter deviceAdapter;
    private ApiClient apiClient;
    
    private List<Room> rooms = new ArrayList<>();
    private List<Device> devices = new ArrayList<>();
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        initializeViews();
        setupToolbar();
        setupDrawer();
        setupRecyclerViews();
        
        apiClient = ApiClient.getInstance(this);
        
        // Load initial data
        loadData();
    }
    
    private void initializeViews() {
        drawerLayout = findViewById(R.id.drawer_layout);
        navigationView = findViewById(R.id.navigation_view);
        toolbar = findViewById(R.id.toolbar);
        swipeRefresh = findViewById(R.id.swipeRefresh);
        tvSecurityStatus = findViewById(R.id.tvSecurityStatus);
        rvRooms = findViewById(R.id.rvRooms);
        rvQuickControls = findViewById(R.id.rvQuickControls);
    }
    
    private void setupToolbar() {
        setSupportActionBar(toolbar);
    }
    
    private void setupDrawer() {
        ActionBarDrawerToggle toggle = new ActionBarDrawerToggle(
            this, drawerLayout, toolbar, R.string.app_name, R.string.app_name);
        drawerLayout.addDrawerListener(toggle);
        toggle.syncState();
        
        navigationView.setNavigationItemSelectedListener(this);
    }
    
    private void setupRecyclerViews() {
        // Setup rooms recycler view
        roomAdapter = new RoomAdapter(rooms, room -> {
            // Handle room click - navigate to room details
            Intent intent = new Intent(this, RoomActivity.class);
            intent.putExtra("room_name", room.getName());
            startActivity(intent);
        });
        rvRooms.setLayoutManager(new LinearLayoutManager(this));
        rvRooms.setAdapter(roomAdapter);
        
        // Setup quick controls recycler view
        deviceAdapter = new DeviceAdapter(devices, device -> {
            // Handle device toggle
            toggleDevice(device);
        });
        rvQuickControls.setLayoutManager(new LinearLayoutManager(this, LinearLayoutManager.HORIZONTAL, false));
        rvQuickControls.setAdapter(deviceAdapter);
        
        // Setup swipe to refresh
        swipeRefresh.setOnRefreshListener(this::loadData);
    }
    
    private void loadData() {
        swipeRefresh.setRefreshing(true);
        loadRooms();
        loadDevices();
        loadSecurityStatus();
    }
    
    private void loadRooms() {
        apiClient.getApiService().getRooms().enqueue(new Callback<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Room>>>() {
            @Override
            public void onResponse(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Room>>> call, 
                                 Response<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Room>>> response) {
                if (response.isSuccessful() && response.body() != null && response.body().isSuccess()) {
                    rooms.clear();
                    if (response.body().data != null) {
                        rooms.addAll(response.body().data);
                    }
                    roomAdapter.notifyDataSetChanged();
                }
                checkLoadingComplete();
            }
            
            @Override
            public void onFailure(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Room>>> call, Throwable t) {
                Toast.makeText(MainActivity.this, "Błąd ładowania pokoi: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                checkLoadingComplete();
            }
        });
    }
    
    private void loadDevices() {
        apiClient.getApiService().getDevices().enqueue(new Callback<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Device>>>() {
            @Override
            public void onResponse(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Device>>> call, 
                                 Response<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Device>>> response) {
                if (response.isSuccessful() && response.body() != null && response.body().isSuccess()) {
                    devices.clear();
                    if (response.body().data != null) {
                        devices.addAll(response.body().data);
                    }
                    deviceAdapter.notifyDataSetChanged();
                }
                checkLoadingComplete();
            }
            
            @Override
            public void onFailure(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<List<Device>>> call, Throwable t) {
                Toast.makeText(MainActivity.this, "Błąd ładowania urządzeń: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                checkLoadingComplete();
            }
        });
    }
    
    private void loadSecurityStatus() {
        apiClient.getApiService().getSecurityState().enqueue(new Callback<com.smarthome.services.SmartHomeApiService.ApiResponse<SecurityStateResponse>>() {
            @Override
            public void onResponse(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<SecurityStateResponse>> call, 
                                 Response<com.smarthome.services.SmartHomeApiService.ApiResponse<SecurityStateResponse>> response) {
                if (response.isSuccessful() && response.body() != null && response.body().isSuccess()) {
                    SecurityStateResponse securityData = response.body().data;
                    if (securityData != null) {
                        tvSecurityStatus.setText(securityData.getSecurityState());
                    } else {
                        tvSecurityStatus.setText("Nieznany");
                    }
                }
                checkLoadingComplete();
            }
            
            @Override
            public void onFailure(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<SecurityStateResponse>> call, Throwable t) {
                tvSecurityStatus.setText("Błąd");
                checkLoadingComplete();
            }
        });
    }
    
    private void toggleDevice(Device device) {
        apiClient.getApiService().toggleDevice(device.getId()).enqueue(new Callback<com.smarthome.services.SmartHomeApiService.ApiResponse<String>>() {
            @Override
            public void onResponse(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<String>> call, 
                                 Response<com.smarthome.services.SmartHomeApiService.ApiResponse<String>> response) {
                if (response.isSuccessful() && response.body() != null && response.body().isSuccess()) {
                    // Toggle the device state locally
                    device.setState(!device.isState());
                    deviceAdapter.notifyDataSetChanged();
                    Toast.makeText(MainActivity.this, "Urządzenie przełączone", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(MainActivity.this, "Błąd przełączania urządzenia", Toast.LENGTH_SHORT).show();
                }
            }
            
            @Override
            public void onFailure(Call<com.smarthome.services.SmartHomeApiService.ApiResponse<String>> call, Throwable t) {
                Toast.makeText(MainActivity.this, "Błąd połączenia: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void checkLoadingComplete() {
        // Stop refreshing when all loads are complete (simplified)
        swipeRefresh.setRefreshing(false);
    }
    
    @Override
    public boolean onNavigationItemSelected(MenuItem item) {
        int id = item.getItemId();
        
        if (id == R.id.nav_dashboard) {
            // Already on dashboard
        } else if (id == R.id.nav_rooms) {
            // Navigate to rooms activity
        } else if (id == R.id.nav_temperature) {
            // Navigate to temperature activity
        } else if (id == R.id.nav_security) {
            // Navigate to security activity
        } else if (id == R.id.nav_settings) {
            Intent intent = new Intent(this, SettingsActivity.class);
            startActivity(intent);
        } else if (id == R.id.nav_logout) {
            logout();
        }
        
        drawerLayout.closeDrawer(GravityCompat.START);
        return true;
    }
    
    private void logout() {
        apiClient.clearSession();
        Intent intent = new Intent(this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
    
    @Override
    public void onBackPressed() {
        if (drawerLayout.isDrawerOpen(GravityCompat.START)) {
            drawerLayout.closeDrawer(GravityCompat.START);
        } else {
            super.onBackPressed();
        }
    }
}