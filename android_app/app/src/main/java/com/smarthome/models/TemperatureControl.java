package com.smarthome.models;

import com.google.gson.annotations.SerializedName;

public class TemperatureControl {
    private String id;
    private String name;
    private String room;
    
    // Server returns single "temperature" field, map it to both current and target
    @SerializedName("temperature")
    private double temperature;
    
    private boolean state = true; // Default active state
    private String mode = "auto"; // Default mode
    private int position = 0; // Default position

    public TemperatureControl() {}

    public TemperatureControl(String id, String name, String room, double currentTemperature, 
                            double targetTemperature, boolean state, String mode, int position) {
        this.id = id;
        this.name = name;
        this.room = room;
        this.temperature = currentTemperature;
        this.state = state;
        this.mode = mode;
        this.position = position;
    }

    // Getters and setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getRoom() { return room; }
    public void setRoom(String room) { this.room = room; }

    // Both current and target temperature return the same value from server
    public double getCurrentTemperature() { return temperature; }
    public void setCurrentTemperature(double currentTemperature) { 
        this.temperature = currentTemperature;
    }

    public double getTargetTemperature() { return temperature; }
    public void setTargetTemperature(double targetTemperature) { 
        this.temperature = targetTemperature; 
    }
    
    // Direct access to temperature field
    public double getTemperature() { return temperature; }
    public void setTemperature(double temperature) { this.temperature = temperature; }

    public boolean isState() { return state; }
    public void setState(boolean state) { this.state = state; }

    public String getMode() { return mode; }
    public void setMode(String mode) { this.mode = mode; }

    public int getPosition() { return position; }
    public void setPosition(int position) { this.position = position; }
}