package com.smarthome.models;

public class TemperatureControl {
    private String id;
    private String name;
    private String room;
    private double currentTemperature;
    private double targetTemperature;
    private boolean state;
    private String mode;
    private int position;

    public TemperatureControl() {}

    public TemperatureControl(String id, String name, String room, double currentTemperature, 
                            double targetTemperature, boolean state, String mode, int position) {
        this.id = id;
        this.name = name;
        this.room = room;
        this.currentTemperature = currentTemperature;
        this.targetTemperature = targetTemperature;
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

    public double getCurrentTemperature() { return currentTemperature; }
    public void setCurrentTemperature(double currentTemperature) { this.currentTemperature = currentTemperature; }

    public double getTargetTemperature() { return targetTemperature; }
    public void setTargetTemperature(double targetTemperature) { this.targetTemperature = targetTemperature; }

    public boolean isState() { return state; }
    public void setState(boolean state) { this.state = state; }

    public String getMode() { return mode; }
    public void setMode(String mode) { this.mode = mode; }

    public int getPosition() { return position; }
    public void setPosition(int position) { this.position = position; }
}