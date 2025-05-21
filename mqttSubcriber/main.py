import time
from mqtt_handle import MQTTHandler
from database import EmotiBitDatabase
import json
from datetime import datetime

db = EmotiBitDatabase()
db_connected = db.connect()

active_devices = {}

ACTIVITY_THRESHOLD = 60  # 1 minute

def process_emotibit_data(topic, payload):
    """Custom callback function to process EmotiBit data"""
    # Extract device ID from topic
    if topic.startswith("Emotibit/"):
        device_id = topic.split("/")[1]
        
        # Update device activity status - this line was missing
        current_time = datetime.now()
        was_inactive = device_id not in active_devices
        active_devices[device_id] = current_time
        
        if was_inactive and db_connected:
            save_device_status(device_id, "active")
            print(f"Device {device_id} is now ACTIVE")
        
        print(f"Processing data from device: {device_id}")
        
        # You could parse JSON data and process it further
        try:
            data = json.loads(payload)
            # Process your data here
            if "sensors" in data:
                if "skintemp" in data["sensors"]:
                    print(f"Temperature: {data['sensors']['skintemp']}°C")
                if "ppg" in data["sensors"]:
                    print(f"PPG samples: {len(data['sensors']['ppg'])}")
                if "eda" in data["sensors"]:
                    print(f"EDA samples: {len(data['sensors']['eda'])}")
            
            if db_connected:

                if "device_id" not in data:
                    data["device_id"] = device_id

                if "timestamp" not in data:
                    data["timestamp"] = int(time.time())

                # Save to database
                success = db.save_sensor_data(topic, payload)
                if success:
                    print(f"Data saved to database for device {device_id}")
                else:
                    print(f"Failed to save data for device {device_id}")
                
        except json.JSONDecodeError:
            print("Received message is not valid JSON")
        except Exception as e:
            print(f"Error processing data: {e}")

def check_device_status():
    current_time = datetime.now()
    inactive_devices = []

    for device_id, last_active in list(active_devices.items()):
        time_diff = (current_time - last_active).total_seconds()
        if time_diff > ACTIVITY_THRESHOLD:
            print(f"Device {device_id} is inactive for {time_diff:.1f} seconds")
            inactive_devices.append(device_id)
    
    for device_id in inactive_devices:
        if db_connected:
            save_device_status(device_id, "inactive")
            print(f"Device {device_id} marked as INACTIVE")
        del active_devices[device_id]
    
    return len(active_devices)

def save_device_status(device_id, status):
    """Save device status to database"""
    timestamp = int(time.time())
    try:
        success = db.save_device_status(device_id, status, timestamp)
        if success:
            print(f"Status '{status}' saved to database for device {device_id}")
        else:
            print(f"Failed to save status for device {device_id}")
    except Exception as e:
        print(f"Error saving device status: {e}")

# Create MQTT handler
mqtt_handler = MQTTHandler()

# Add custom callback
mqtt_handler.add_callback(process_emotibit_data)

# Connect and start
if mqtt_handler.connect():
    mqtt_handler.start()
    
    try:
        print("EmotiBit MQTT Subscriber running. Press Ctrl+C to stop.")
        last_status_check = time.time()

        # Main application loop
        while True:
            messages = mqtt_handler.get_latest_message()

            # Check device status every 5 seconds
            current_time = time.time()
            if current_time - last_status_check >= 5:
                active_count = check_device_status()
                print(f"Status: {active_count} active EmotiBit device(s)")
                last_status_check = current_time
            
            # Sleep to avoid high CPU usage
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping application...")
    finally:
        mqtt_handler.stop()
        if db_connected:
            db.close()
else:
    print("Failed to connect to MQTT broker, exiting.")