package com.smarthome.services;

import com.smarthome.models.Device;
import com.smarthome.models.Room;
import com.smarthome.models.SecurityStateResponse;
import com.smarthome.models.SecurityToggleRequest;
import com.smarthome.models.TemperatureControl;
import com.smarthome.models.User;

import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.DELETE;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.PUT;
import retrofit2.http.Path;

public interface SmartHomeApiService {
    
    // Connection testing
    @GET("api/ping")
    Call<ApiResponse<String>> ping();
    
    @GET("api/status")
    Call<ApiResponse<ServerStatus>> getServerStatus();
    
    // Authentication
    @POST("login")
    Call<ApiResponse<LoginResponse>> login(@Body LoginRequest request);
    
    @POST("logout")
    Call<ApiResponse<String>> logout();
    
    // User management
    @GET("api/user/profile")
    Call<ApiResponse<User>> getUserProfile();
    
    @PUT("api/user/profile")
    Call<ApiResponse<User>> updateUserProfile(@Body User user);
    
    // Rooms
    @GET("api/rooms")
    Call<ApiResponse<List<Room>>> getRooms();
    
    @POST("api/rooms")
    Call<ApiResponse<Room>> createRoom(@Body Room room);
    
    @PUT("api/rooms/{room}")
    Call<ApiResponse<Room>> updateRoom(@Path("room") String roomId, @Body Room room);
    
    @DELETE("api/rooms/{room}")
    Call<ApiResponse<String>> deleteRoom(@Path("room") String roomId);
    
    // Devices/Buttons
    @GET("api/buttons")
    Call<ApiResponse<List<Device>>> getDevices();
    
    @POST("api/buttons")
    Call<ApiResponse<Device>> createDevice(@Body Device device);
    
    @PUT("api/buttons/{id}")
    Call<ApiResponse<Device>> updateDevice(@Path("id") String deviceId, @Body Device device);
    
    @DELETE("api/buttons/{id}")
    Call<ApiResponse<String>> deleteDevice(@Path("id") String deviceId);
    
    @POST("api/buttons/{id}/toggle")
    Call<ApiResponse<String>> toggleDevice(@Path("id") String deviceId);
    
    // Temperature controls
    @GET("api/temperature_controls")
    Call<ApiResponse<List<TemperatureControl>>> getTemperatureControls();
    
    @POST("api/temperature_controls")
    Call<ApiResponse<TemperatureControl>> createTemperatureControl(@Body TemperatureControl control);
    
    @PUT("api/temperature_controls/{id}")
    Call<ApiResponse<TemperatureControl>> updateTemperatureControl(@Path("id") String controlId, @Body TemperatureControl control);
    
    @DELETE("api/temperature_controls/{id}")
    Call<ApiResponse<String>> deleteTemperatureControl(@Path("id") String controlId);
    
    // Security
    @GET("api/security")
    Call<ApiResponse<SecurityStateResponse>> getSecurityState();
    
    @POST("api/security")
    Call<ApiResponse<SecurityStateResponse>> toggleSecurity(@Body SecurityToggleRequest request);

    // Inner classes for API requests and responses
    class LoginRequest {
        public String username;
        public String password;
        
        public LoginRequest(String username, String password) {
            this.username = username;
            this.password = password;
        }
    }
    
    class LoginResponse {
        public String status;
        public String message;
        public User user;
        public String session_id;
    }
    
    class ApiResponse<T> {
        public String status;
        public String message;
        public T data;
        
        public boolean isSuccess() {
            return "success".equals(status);
        }
    }
    
    class ServerStatus {
        public String server_status;
        public boolean database_mode;
        public long timestamp;
    }
}