package com.smarthome.models;

import com.google.gson.annotations.SerializedName;

public class SecurityStateResponse {
    @SerializedName("security_state")
    private String securityState;
    
    // Constructors
    public SecurityStateResponse() {}
    
    public SecurityStateResponse(String securityState) {
        this.securityState = securityState;
    }
    
    // Getters and setters
    public String getSecurityState() {
        return securityState;
    }
    
    public void setSecurityState(String securityState) {
        this.securityState = securityState;
    }
    
    // Helper methods
    public boolean isEnabled() {
        return "Załączony".equals(securityState);
    }
    
    public boolean isDisabled() {
        return "Wyłączony".equals(securityState);
    }
    
    @Override
    public String toString() {
        return "SecurityStateResponse{" +
                "securityState='" + securityState + '\'' +
                '}';
    }
}
