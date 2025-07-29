package com.smarthome.utils;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.button.MaterialButton;
import com.smarthome.R;
import com.smarthome.models.TemperatureControl;

import java.util.List;

public class TemperatureControlAdapter extends RecyclerView.Adapter<TemperatureControlAdapter.TemperatureControlViewHolder> {
    
    private List<TemperatureControl> temperatureControls;
    private OnTemperatureControlClickListener listener;
    
    public interface OnTemperatureControlClickListener {
        void onTemperatureControlClick(TemperatureControl control);
    }
    
    public TemperatureControlAdapter(List<TemperatureControl> temperatureControls, OnTemperatureControlClickListener listener) {
        this.temperatureControls = temperatureControls;
        this.listener = listener;
    }
    
    @NonNull
    @Override
    public TemperatureControlViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_temperature_control, parent, false);
        return new TemperatureControlViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull TemperatureControlViewHolder holder, int position) {
        TemperatureControl control = temperatureControls.get(position);
        
        holder.tvName.setText(control.getName());
        holder.tvRoom.setText(control.getRoom());
        holder.tvCurrentTemp.setText(String.format("%.1f°C", control.getCurrentTemperature()));
        holder.tvTargetTemp.setText(String.format("%.1f°C", control.getTargetTemperature()));
        
        // Set icon color based on active state
        if (control.isState()) {
            holder.ivIcon.setColorFilter(holder.itemView.getContext().getColor(R.color.md_theme_primary));
        } else {
            holder.ivIcon.setColorFilter(holder.itemView.getContext().getColor(R.color.md_theme_outline));
        }
        
        holder.btnAdjust.setOnClickListener(v -> {
            if (listener != null) {
                listener.onTemperatureControlClick(control);
            }
        });
    }
    
    @Override
    public int getItemCount() {
        return temperatureControls.size();
    }
    
    static class TemperatureControlViewHolder extends RecyclerView.ViewHolder {
        ImageView ivIcon;
        TextView tvName;
        TextView tvRoom;
        TextView tvCurrentTemp;
        TextView tvTargetTemp;
        MaterialButton btnAdjust;
        
        public TemperatureControlViewHolder(@NonNull View itemView) {
            super(itemView);
            ivIcon = itemView.findViewById(R.id.ivTemperatureIcon);
            tvName = itemView.findViewById(R.id.tvTemperatureName);
            tvRoom = itemView.findViewById(R.id.tvTemperatureRoom);
            tvCurrentTemp = itemView.findViewById(R.id.tvCurrentTemp);
            tvTargetTemp = itemView.findViewById(R.id.tvTargetTemp);
            btnAdjust = itemView.findViewById(R.id.btnAdjustTemp);
        }
    }
}
