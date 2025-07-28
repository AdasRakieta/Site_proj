package com.smarthome.models;

public class Device {
    private String id;
    private String name;
    private String room;
    private String type;
    private boolean state;
    private String color;
    private int position;

    public Device() {}

    public Device(String id, String name, String room, String type, boolean state, String color, int position) {
        this.id = id;
        this.name = name;
        this.room = room;
        this.type = type;
        this.state = state;
        this.color = color;
        this.position = position;
    }

    // Getters and setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getRoom() { return room; }
    public void setRoom(String room) { this.room = room; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public boolean isState() { return state; }
    public void setState(boolean state) { this.state = state; }

    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }

    public int getPosition() { return position; }
    public void setPosition(int position) { this.position = position; }
}