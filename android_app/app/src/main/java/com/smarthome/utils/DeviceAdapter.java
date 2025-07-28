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
import com.smarthome.models.Device;

import java.util.List;

public class DeviceAdapter extends RecyclerView.Adapter<DeviceAdapter.DeviceViewHolder> {
    
    private List<Device> devices;
    private OnDeviceClickListener listener;
    
    public interface OnDeviceClickListener {
        void onDeviceClick(Device device);
    }
    
    public DeviceAdapter(List<Device> devices, OnDeviceClickListener listener) {
        this.devices = devices;
        this.listener = listener;
    }
    
    @NonNull
    @Override
    public DeviceViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_device, parent, false);
        return new DeviceViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull DeviceViewHolder holder, int position) {
        Device device = devices.get(position);
        holder.bind(device, listener);
    }
    
    @Override
    public int getItemCount() {
        return devices.size();
    }
    
    static class DeviceViewHolder extends RecyclerView.ViewHolder {
        private MaterialButton btnDevice;
        private TextView tvDeviceName;
        private TextView tvDeviceRoom;
        private ImageView ivDeviceIcon;
        
        public DeviceViewHolder(@NonNull View itemView) {
            super(itemView);
            btnDevice = itemView.findViewById(R.id.btnDevice);
            tvDeviceName = itemView.findViewById(R.id.tvDeviceName);
            tvDeviceRoom = itemView.findViewById(R.id.tvDeviceRoom);
            ivDeviceIcon = itemView.findViewById(R.id.ivDeviceIcon);
        }
        
        public void bind(Device device, OnDeviceClickListener listener) {
            tvDeviceName.setText(device.getName());
            tvDeviceRoom.setText(device.getRoom());
            
            // Set device icon based on type
            setDeviceIcon(device);
            
            // Set button appearance based on state
            updateDeviceState(device);
            
            btnDevice.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onDeviceClick(device);
                }
            });
        }
        
        private void setDeviceIcon(Device device) {
            String type = device.getType();
            if (type != null) {
                switch (type.toLowerCase()) {
                    case "light":
                    case "światło":
                        ivDeviceIcon.setImageResource(R.drawable.ic_lightbulb);
                        break;
                    case "fan":
                    case "wentylator":
                        ivDeviceIcon.setImageResource(R.drawable.ic_fan);
                        break;
                    case "switch":
                    case "przełącznik":
                        ivDeviceIcon.setImageResource(R.drawable.ic_switch);
                        break;
                    default:
                        ivDeviceIcon.setImageResource(R.drawable.ic_device);
                        break;
                }
            } else {
                ivDeviceIcon.setImageResource(R.drawable.ic_device);
            }
        }
        
        private void updateDeviceState(Device device) {
            if (device.isState()) {
                btnDevice.setBackgroundColor(itemView.getContext().getColor(R.color.device_on));
                btnDevice.setText("WŁĄCZONY");
            } else {
                btnDevice.setBackgroundColor(itemView.getContext().getColor(R.color.device_off));
                btnDevice.setText("WYŁĄCZONY");
            }
        }
    }
}