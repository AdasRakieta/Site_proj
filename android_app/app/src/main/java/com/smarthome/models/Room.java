package com.smarthome.models;

public class Room {
    private String id;
    private String name;
    private String color;
    private int position;

    public Room() {}

    public Room(String id, String name, String color, int position) {
        this.id = id;
        this.name = name;
        this.color = color;
        this.position = position;
    }

    // Getters and setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }

    public int getPosition() { return position; }
    public void setPosition(int position) { this.position = position; }
}