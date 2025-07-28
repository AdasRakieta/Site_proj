package com.smarthome.models;

import com.google.gson.annotations.SerializedName;

public class SecurityToggleRequest {
    @SerializedName("state")
    private String state;
    
    // Constructors
    public SecurityToggleRequest() {}
    
    public SecurityToggleRequest(String state) {
        this.state = state;
    }
    
    public SecurityToggleRequest(boolean enabled) {
        this.state = enabled ? "Załączony" : "Wyłączony";
    }
    
    // Getters and setters
    public String getState() {
        return state;
    }
    
    public void setState(String state) {
        this.state = state;
    }
    
    public void setEnabled(boolean enabled) {
        this.state = enabled ? "Załączony" : "Wyłączony";
    }
    
    // Helper methods
    public boolean isEnabled() {
        return "Załączony".equals(state);
    }
    
    public static SecurityToggleRequest createEnabled() {
        return new SecurityToggleRequest("Załączony");
    }
    
    public static SecurityToggleRequest createDisabled() {
        return new SecurityToggleRequest("Wyłączony");
    }
    
    @Override
    public String toString() {
        return "SecurityToggleRequest{" +
                "state='" + state + '\'' +
                '}';
    }
}
