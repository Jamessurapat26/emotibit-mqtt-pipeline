# handle mqtt
import paho.mqtt.client as mqtt
import time
import json

class MQTTHandler:
    def __init__(self, broker="broker.emqx.io", port=1883, keep_alive=60):
        """Initialize the MQTT handler with broker configuration"""
        # Broker configuration
        self.broker_address = broker
        self.port = port
        self.keep_alive = keep_alive
        
        # Create MQTT client instance
        self.client = mqtt.Client()
        
        # Set default callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Subscription topics
        self.subscription_topic = "Emotibit/#"  # Default subscription to all Emotibit topics
        
        # Message storage for data access from main application
        self.latest_messages = {}  # Topic -> Message dictionary
        self.callbacks = []  # List of custom callback functions 
        
    def connect(self):
        """Connect to the MQTT broker"""
        try:
            print(f"Connecting to MQTT broker at {self.broker_address}...")
            self.client.connect(self.broker_address, self.port, self.keep_alive)
            return True
        except Exception as e:
            print(f"Error connecting to broker: {e}")
            return False
            
    def start(self):
        """Start the MQTT client loop in a non-blocking way"""
        self.client.loop_start()
        
    def stop(self):
        """Stop the MQTT client loop and disconnect"""
        self.client.loop_stop()
        self.client.disconnect()
        print("Disconnected from MQTT broker")
        
    def subscribe(self, topic=None):
        """Subscribe to a specific topic or use default"""
        if topic:
            self.subscription_topic = topic
        self.client.subscribe(self.subscription_topic)
        print(f"Subscribed to {self.subscription_topic}")
        
    def add_callback(self, callback_function):
        """Add a custom callback function to be called with received messages"""
        self.callbacks.append(callback_function)
        
    def get_latest_message(self, topic=None):
        """Get the latest message for a specific topic or all messages"""
        if topic:
            return self.latest_messages.get(topic)
        return self.latest_messages
    
    def _on_connect(self, client, userdata, flags, rc):
        """Internal callback for connection"""
        if rc == 0:
            print("Successfully connected to MQTT broker")
            # Subscribe to all configured topics
            self.subscribe()
        else:
            print(f"Failed to connect, return code: {rc}")
            
    def _on_message(self, client, userdata, msg):
        """Internal callback for message reception"""
        try:
            # Decode the payload
            payload = msg.payload.decode()
            
            # Store the latest message for this topic
            self.latest_messages[msg.topic] = payload
            
            # Print received message
            print(f"Received message on {msg.topic}: {payload}")
            
            # Call any custom callbacks
            for callback in self.callbacks:
                try:
                    callback(msg.topic, payload)
                except Exception as e:
                    print(f"Error in custom callback: {e}")
                
        except Exception as e:
            print(f"Error processing message: {e}")
            
    def _on_disconnect(self, client, userdata, rc):
        """Internal callback for disconnection"""
        print(f"Disconnected with result code {rc}")
        if rc != 0:
            print("Unexpected disconnection. Attempting to reconnect...")
            
    def set_custom_callbacks(self, on_connect=None, on_message=None, on_disconnect=None):
        """Set custom callbacks instead of the default ones"""
        if on_connect:
            self.client.on_connect = on_connect
        if on_message:
            self.client.on_message = on_message
        if on_disconnect:
            self.client.on_disconnect = on_disconnect

# Simple usage example - this only runs if the file is executed directly
if __name__ == "__main__":
    # Create handler
    mqtt_handler = MQTTHandler()
    
    # Connect and start
    if mqtt_handler.connect():
        mqtt_handler.start()
        
        try:
            print("MQTT handler running. Press Ctrl+C to stop.")
            # Keep the program running to receive messages
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping MQTT handler...")
        finally:
            mqtt_handler.stop()

