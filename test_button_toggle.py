#!/usr/bin/env python3
"""
Test script to debug button toggle functionality.
"""

from utils.multi_home_db_manager import MultiHomeDBManager

def test_button_toggle():
    """Test button toggle functionality directly"""
    try:
        # Initialize multi-home DB manager
        multi_db = MultiHomeDBManager()
        
        # Test data
        user_id = '727a5147-14e6-405d-921b-931fbc0397ed'  # admin user
        home_id = '40a67bc7-6b5d-4a88-bce1-f7ef6d06432c'  # Admin Home
        
        print("1. Getting buttons from Admin Home...")
        buttons = multi_db.get_buttons(home_id, user_id)
        print(f"   Found {len(buttons)} buttons:")
        for button in buttons:
            print(f"     - ID: {button['id']}, Name: {button['name']}, Room: {button['room_name']}, State: {button['state']}")
        
        if buttons:
            # Test get_device
            button_id = buttons[0]['id']
            print(f"\n2. Testing get_device for button ID {button_id}...")
            device = multi_db.get_device(button_id, user_id)
            if device:
                print(f"   Device found: {device['name']}, current state: {device['state']}")
                
                # Test update_device
                new_state = not device['state']
                print(f"\n3. Testing update_device: changing state from {device['state']} to {new_state}...")
                success = multi_db.update_device(button_id, user_id, state=new_state)
                print(f"   Update result: {success}")
                
                # Verify update
                print(f"\n4. Verifying update...")
                updated_device = multi_db.get_device(button_id, user_id)
                if updated_device:
                    print(f"   Updated device state: {updated_device['state']}")
                    if updated_device['state'] == new_state:
                        print("   ✅ Update successful!")
                    else:
                        print("   ❌ Update failed - state didn't change")
                else:
                    print("   ❌ Could not retrieve updated device")
            else:
                print(f"   ❌ Device not found with ID {button_id}")
        else:
            print("   ❌ No buttons found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_button_toggle()