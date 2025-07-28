package com.smarthome.utils;

import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.card.MaterialCardView;
import com.smarthome.R;
import com.smarthome.models.Room;

import java.util.List;

public class RoomAdapter extends RecyclerView.Adapter<RoomAdapter.RoomViewHolder> {
    
    private List<Room> rooms;
    private OnRoomClickListener listener;
    
    public interface OnRoomClickListener {
        void onRoomClick(Room room);
    }
    
    public RoomAdapter(List<Room> rooms, OnRoomClickListener listener) {
        this.rooms = rooms;
        this.listener = listener;
    }
    
    @NonNull
    @Override
    public RoomViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_room, parent, false);
        return new RoomViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull RoomViewHolder holder, int position) {
        Room room = rooms.get(position);
        holder.bind(room, listener);
    }
    
    @Override
    public int getItemCount() {
        return rooms.size();
    }
    
    static class RoomViewHolder extends RecyclerView.ViewHolder {
        private MaterialCardView cardView;
        private TextView tvRoomName;
        
        public RoomViewHolder(@NonNull View itemView) {
            super(itemView);
            cardView = itemView.findViewById(R.id.cardRoom);
            tvRoomName = itemView.findViewById(R.id.tvRoomName);
        }
        
        public void bind(Room room, OnRoomClickListener listener) {
            tvRoomName.setText(room.getName());
            
            // Set room color if available
            if (room.getColor() != null && !room.getColor().isEmpty()) {
                try {
                    int color = Color.parseColor(room.getColor());
                    cardView.setCardBackgroundColor(color);
                } catch (IllegalArgumentException e) {
                    // Use default color if parsing fails
                    cardView.setCardBackgroundColor(itemView.getContext().getColor(R.color.md_theme_surface));
                }
            }
            
            cardView.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onRoomClick(room);
                }
            });
        }
    }
}