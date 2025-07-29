package com.smarthome.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.MenuItem;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.ActionBarDrawerToggle;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.GravityCompat;
import androidx.drawerlayout.widget.DrawerLayout;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.widget.EditText;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import com.google.android.material.appbar.MaterialToolbar;
import com.google.android.material.navigation.NavigationView;
import com.smarthome.R;
import com.smarthome.models.Device;
import com.smarthome.models.Room;
import com.smarthome.models.SecurityStateResponse;
import com.smarthome.models.TemperatureControl;
import com.smarthome.models.TemperatureSetRequest;
import com.smarthome.services.ApiClient;
import com.smarthome.services.SmartHomeApiService;
import com.smarthome.utils.DeviceAdapter;
import com.smarthome.utils.RoomAdapter;
import com.smarthome.utils.TemperatureControlAdapter;

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
    private RecyclerView rvTemperatureControls;
    
    private RoomAdapter roomAdapter;
    private DeviceAdapter deviceAdapter;
    private TemperatureControlAdapter temperatureControlAdapter;
    private ApiClient apiClient;
    
    private List<Room> rooms = new ArrayList<>();
    private List<Device> devices = new ArrayList<>();
    private List<TemperatureControl> temperatureControls = new ArrayList<>();
    
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
        rvTemperatureControls = findViewById(R.id.rvTemperatureControls);
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
        
        // Setup temperature controls recycler view
        temperatureControlAdapter = new TemperatureControlAdapter(temperatureControls, control -> {
            // Handle temperature control click - show temperature adjustment dialog
            showTemperatureDialog(control);
        });
        rvTemperatureControls.setLayoutManager(new LinearLayoutManager(this));
        rvTemperatureControls.setAdapter(temperatureControlAdapter);
        
        // Setup swipe to refresh
        swipeRefresh.setOnRefreshListener(this::loadData);
    }
    
    private void loadData() {
        swipeRefresh.setRefreshing(true);
        loadRooms();
        loadDevices();
        loadTemperatureControls();
        loadSecurityStatus();
    }
    
    private void loadRooms() {
        apiClient.getApiService().getRooms().enqueue(new Callback<List<String>>() {
            @Override
            public void onResponse(Call<List<String>> call, Response<List<String>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    rooms.clear();
                    for (String name : response.body()) {
                        rooms.add(new Room(name, name, "#2196F3", 0));
                    }
                    roomAdapter.notifyDataSetChanged();
                }
                checkLoadingComplete();
            }
            
            @Override
            public void onFailure(Call<List<String>> call, Throwable t) {
                Toast.makeText(MainActivity.this, "Błąd ładowania pokoi: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                checkLoadingComplete();
            }
        });
    }
    
    private void loadDevices() {
        apiClient.getApiService().getDevices().enqueue(new Callback<List<Device>>() {
            @Override
            public void onResponse(Call<List<Device>> call, Response<List<Device>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    devices.clear();
                    devices.addAll(response.body());
                    deviceAdapter.notifyDataSetChanged();
                }
                checkLoadingComplete();
            }
            
            @Override
            public void onFailure(Call<List<Device>> call, Throwable t) {
                Toast.makeText(MainActivity.this, "Błąd ładowania urządzeń: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                checkLoadingComplete();
            }
        });
    }
    
    private void loadTemperatureControls() {
        android.util.Log.d("MainActivity", "Loading temperature controls...");
        apiClient.getApiService().getTemperatureControls().enqueue(new Callback<SmartHomeApiService.ApiResponse<List<TemperatureControl>>>() {
            @Override
            public void onResponse(Call<SmartHomeApiService.ApiResponse<List<TemperatureControl>>> call, 
                                 Response<SmartHomeApiService.ApiResponse<List<TemperatureControl>>> response) {
                android.util.Log.d("MainActivity", "Temperature controls response code: " + response.code());
                if (response.isSuccessful() && response.body() != null) {
                    android.util.Log.d("MainActivity", "Response successful. Body: " + response.body().status);
                    if (response.body().isSuccess()) {
                        temperatureControls.clear();
                        if (response.body().data != null) {
                            temperatureControls.addAll(response.body().data);
                            temperatureControlAdapter.notifyDataSetChanged();
                            // Log kontrolek temperatury dla debugowania
                            android.util.Log.d("MainActivity", "Załadowano " + temperatureControls.size() + " termostatów");
                            for (TemperatureControl control : temperatureControls) {
                                android.util.Log.d("MainActivity", "Termostat: " + control.getName() + " w pokoju: " + control.getRoom() + ", temp: " + control.getTemperature());
                            }
                        } else {
                            android.util.Log.w("MainActivity", "Temperature controls data is null");
                        }
                    } else {
                        android.util.Log.e("MainActivity", "API response indicates failure: " + response.body().message);
                        Toast.makeText(MainActivity.this, "API error: " + response.body().message, Toast.LENGTH_SHORT).show();
                    }
                } else {
                    Toast.makeText(MainActivity.this, "Błąd ładowania termostatów", Toast.LENGTH_SHORT).show();
                    android.util.Log.e("MainActivity", "Response not successful: " + response.code());
                    if (response.errorBody() != null) {
                        try {
                            android.util.Log.e("MainActivity", "Error body: " + response.errorBody().string());
                        } catch (Exception e) {
                            android.util.Log.e("MainActivity", "Error reading error body", e);
                        }
                    }
                }
                checkLoadingComplete();
            }
            
            @Override
            public void onFailure(Call<SmartHomeApiService.ApiResponse<List<TemperatureControl>>> call, Throwable t) {
                Toast.makeText(MainActivity.this, "Błąd ładowania termostatów: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                android.util.Log.e("MainActivity", "Błąd ładowania termostatów", t);
                checkLoadingComplete();
            }
        });
    }
    
    private void loadSecurityStatus() {
        android.util.Log.d("MainActivity", "Loading security status...");
        apiClient.getApiService().getSecurityState().enqueue(new Callback<SecurityStateResponse>() {
            @Override
            public void onResponse(Call<SecurityStateResponse> call, Response<SecurityStateResponse> response) {
                android.util.Log.d("MainActivity", "Security response code: " + response.code());
                if (response.isSuccessful() && response.body() != null) {
                    SecurityStateResponse securityData = response.body();
                    android.util.Log.d("MainActivity", "Security state received: " + securityData.getSecurityState());
                    if (securityData.getSecurityState() != null) {
                        tvSecurityStatus.setText(securityData.getSecurityState());
                        android.util.Log.d("MainActivity", "Security status set to: " + securityData.getSecurityState());
                    } else {
                        tvSecurityStatus.setText("Nieznany");
                        android.util.Log.w("MainActivity", "Security state is null");
                    }
                } else {
                    tvSecurityStatus.setText("Błąd");
                    android.util.Log.e("MainActivity", "Security response not successful. Code: " + response.code());
                    if (response.errorBody() != null) {
                        try {
                            android.util.Log.e("MainActivity", "Error body: " + response.errorBody().string());
                        } catch (Exception e) {
                            android.util.Log.e("MainActivity", "Error reading error body", e);
                        }
                    }
                }
                checkLoadingComplete();
            }
            
            @Override
            public void onFailure(Call<SecurityStateResponse> call, Throwable t) {
                tvSecurityStatus.setText("Błąd");
                android.util.Log.e("MainActivity", "Security request failed", t);
                checkLoadingComplete();
            }
        });
    }
    
    private void toggleDevice(Device device) {
        apiClient.getApiService().toggleDevice(device.getId()).enqueue(new Callback<String>() {
            @Override
            public void onResponse(Call<String> call, Response<String> response) {
                if (response.isSuccessful()) {
                    // Toggle the device state locally
                    device.setState(!device.isState());
                    deviceAdapter.notifyDataSetChanged();
                    Toast.makeText(MainActivity.this, "Urządzenie przełączone", Toast.LENGTH_SHORT).show();
                } else {
                    // Handle error response
                    String errorMessage = "Błąd przełączania urządzenia";
                    if (response.code() == 500) {
                        errorMessage = "Błąd serwera - sprawdź połączenie z urządzeniem";
                    }
                    Toast.makeText(MainActivity.this, errorMessage, Toast.LENGTH_SHORT).show();
                }
            }
            
            @Override
            public void onFailure(Call<String> call, Throwable t) {
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
    
    private void showTemperatureDialog(TemperatureControl control) {
        android.app.AlertDialog.Builder builder = new android.app.AlertDialog.Builder(this);
        builder.setTitle("Ustaw temperaturę - " + control.getName());
        
        // Create input field with current target temperature
        final android.widget.EditText input = new android.widget.EditText(this);
        input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        input.setText(String.valueOf(control.getTargetTemperature()));
        input.setHint("Temperatura (16-30°C)");
        
        // Add some padding
        android.widget.LinearLayout.LayoutParams lp = new android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT);
        lp.setMargins(50, 0, 50, 0);
        input.setLayoutParams(lp);
        
        builder.setView(input);
        
        builder.setPositiveButton("Ustaw", (dialog, which) -> {
            String tempStr = input.getText().toString().trim();
            try {
                double newTemp = Double.parseDouble(tempStr);
                if (newTemp >= 16 && newTemp <= 30) {
                    setTemperature(control, newTemp);
                } else {
                    Toast.makeText(this, "Temperatura musi być między 16°C a 30°C", Toast.LENGTH_SHORT).show();
                }
            } catch (NumberFormatException e) {
                Toast.makeText(this, "Wprowadź prawidłową temperaturę", Toast.LENGTH_SHORT).show();
            }
        });
        
        builder.setNegativeButton("Anuluj", (dialog, which) -> dialog.cancel());
        
        builder.show();
    }
    
    private void setTemperature(TemperatureControl control, double temperature) {
        TemperatureSetRequest request = new TemperatureSetRequest(temperature);
        
        Call<SmartHomeApiService.ApiResponse<String>> call = smartHomeApi.setTemperature(control.getId(), request);
        call.enqueue(new Callback<SmartHomeApiService.ApiResponse<String>>() {
            @Override
            public void onResponse(Call<SmartHomeApiService.ApiResponse<String>> call, Response<SmartHomeApiService.ApiResponse<String>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    SmartHomeApiService.ApiResponse<String> apiResponse = response.body();
                    if ("success".equals(apiResponse.status)) {
                        Toast.makeText(MainActivity.this, 
                            "Temperatura ustawiona na " + temperature + "°C", 
                            Toast.LENGTH_SHORT).show();
                        
                        // Odśwież listę termostatów
                        loadTemperatureControls();
                    } else {
                        Toast.makeText(MainActivity.this, 
                            "Błąd: " + (apiResponse.message != null ? apiResponse.message : "Nieznany błąd"), 
                            Toast.LENGTH_SHORT).show();
                    }
                } else {
                    Toast.makeText(MainActivity.this, 
                        "Błąd połączenia z serwerem", 
                        Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<SmartHomeApiService.ApiResponse<String>> call, Throwable t) {
                Toast.makeText(MainActivity.this, 
                    "Błąd sieci: " + t.getMessage(), 
                    Toast.LENGTH_SHORT).show();
            }
        });
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