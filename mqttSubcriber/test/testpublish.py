import paho.mqtt.client as mqtt
import time
import random
import json

# Broker configuration
broker_address = "broker.emqx.io"
port = 1883
keep_alive = 60

# Topic to publish to
base_topic = "Emotibit"

class EmotibitData:
    def __init__(self):
        self.device_id = "Emotibit-001"  # Default device ID
        self.timestamp = 0
        self.sensors = {
            "skintemp": 0.0,
            "eda": [],
            "ppg": []
        } 

    def set_device_id(self, device_id):
        self.device_id = device_id
    
    def generate_data(self):  # Fixed method name from generate_datad to generate_data
        # Clear previous data
        self.sensors["ppg"] = []
        self.sensors["eda"] = []
        
        ppg_sample = 100
        eda_sample = 15
        self.sensors["skintemp"] = round(36.5 + random.uniform(-0.5, 0.5), 2)  # Fix: was "temperature" not matching the initialized "skintemp"
        
        # Fix: incorrect loop syntax - len(range(n)) is just n
        for _ in range(ppg_sample):  # Fixed loop syntax
            self.sensors["ppg"].append(random.randint(0, 1023))
            
        for _ in range(eda_sample):  # Fixed loop syntax
            self.sensors["eda"].append(random.randint(0, 1023))
            
        self.timestamp = int(time.time())
    
    def to_json(self):
        data = {
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "sensors": self.sensors
        }
        return json.dumps(data)
    
    def publish_data(self, client):
        """Generate and publish data to MQTT broker"""
        self.generate_data()  # Now correctly calls generate_data instead of generate_datad
        
        # Publish all data to the device topic
        device_topic = f"{base_topic}/{self.device_id}"
        client.publish(device_topic, self.to_json())
        print(f"Published to {device_topic} - PPG: {len(self.sensors['ppg'])} samples @ 100Hz, EDA: {len(self.sensors['eda'])} samples")
    
# Callback functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Successfully connected to MQTT broker")
    else:
        print(f"Failed to connect, return code: {rc}")

# Create an MQTT client instance
client = mqtt.Client()
client.on_connect = on_connect

try:
    # Connect to the broker
    print(f"Connecting to MQTT broker at {broker_address}...")
    client.connect(broker_address, port, keep_alive)
    
    # Start the loop in a non-blocking way
    client.loop_start()

    emotibit_data = [EmotibitData() for _ in range(2)]
    emotibit_data[0].set_device_id("Emotibit-001")
    emotibit_data[1].set_device_id("MD-V5-0000560")
    
    print("Publishing EmotiBit test data every second. Press Ctrl+C to stop.")
    
    while True:
        for data in emotibit_data:
            data.publish_data(client)
    
        time.sleep(1)
        
        
except KeyboardInterrupt: 
    print("Stopping MQTT publisher...")
except Exception as e:
    print(f"Error: {e}")
finally:
    # Clean up
    client.loop_stop()
    client.disconnect()
    print("Disconnected from broker")