package com.smarthome.models;

public class TemperatureSetRequest {
    private double temperature;

    public TemperatureSetRequest(double temperature) {
        this.temperature = temperature;
    }

    public double getTemperature() {
        return temperature;
    }

    public void setTemperature(double temperature) {
        this.temperature = temperature;
    }
}
