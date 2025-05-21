import pymongo
import json
import time
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables from .env file
load_dotenv()

class EmotiBitDatabase:
    def __init__(self, mongo_uri=None, db_name=None, collection_name=None):
        """Initialize the database connection
        
        Args:
            mongo_uri (str, optional): MongoDB connection string. If None, uses MONGO_URI env var.
            db_name (str, optional): Database name. If None, uses MONGO_DB_NAME env var.
            collection_name (str, optional): Collection name. If None, uses MONGO_COLLECTION env var.
        """
        # Get configuration from environment variables with fallbacks
        self.mongo_uri = mongo_uri or os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.db_name = db_name or os.getenv('MONGO_DB_NAME', 'emotibit_data')
        self.collection_name = collection_name or os.getenv('MONGO_COLLECTION', 'sensor_readings')
        
        # Log configuration (without credentials)
        print(f"Database config: {self.db_name}.{self.collection_name}")
        
        self.client = None
        self.db = None
        self.collection = None
        self.connected = False
        
    async def connect_async(self):
        """Connect to MongoDB database asynchronously"""
        try:
            # Connect to MongoDB using motor async driver
            self.client = AsyncIOMotorClient(self.mongo_uri)
            
            # Get database and collection
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Check connection with a simple operation
            await self.db.command('ping')
            
            # Create indexes for faster querying
            await self.collection.create_index([("device_id", pymongo.ASCENDING)])
            await self.collection.create_index([("timestamp", pymongo.ASCENDING)])
            await self.collection.create_index([("device_id", pymongo.ASCENDING), 
                                          ("timestamp", pymongo.ASCENDING)])
            
            # Create index for device_status collection
            status_collection = self.db["device_status"]
            await status_collection.create_index([("device_id", pymongo.ASCENDING)])
            await status_collection.create_index([("timestamp", pymongo.DESCENDING)])
            
            print(f"Connected to MongoDB: {self.db_name}")
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.connected = False
            return False
    
    # Keep the synchronous version for backward compatibility
    def connect(self):
        """Connect to MongoDB database (synchronous version)"""
        try:
            # Connect to MongoDB
            self.client = pymongo.MongoClient(self.mongo_uri)
            # print("mongo_uri", self.mongo_uri)
            
            # Check connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for faster querying
            self.collection.create_index([("device_id", pymongo.ASCENDING)])
            self.collection.create_index([("timestamp", pymongo.ASCENDING)])
            self.collection.create_index([("device_id", pymongo.ASCENDING), 
                                         ("timestamp", pymongo.ASCENDING)])
            
            # Create index for device_status collection
            status_collection = self.db["device_status"]
            status_collection.create_index([("device_id", pymongo.ASCENDING)])
            status_collection.create_index([("timestamp", pymongo.DESCENDING)])
            
            print(f"Connected to MongoDB: {self.db_name}")
            self.connected = True
            return True
            
        except pymongo.errors.ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            self.connected = False
            return False
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.connected = False
            return False
    
    async def close_async(self):
        """Close database connection asynchronously"""
        if self.client:
            self.client.close()
            self.connected = False
            print("Database connection closed")
    
    def close(self):
        """Close database connection (synchronous version)"""
        if self.client:
            self.client.close()
            self.connected = False
            print("Database connection closed")
    
    async def save_sensor_data_async(self, topic, payload_str):
        """Save sensor data from MQTT message to database asynchronously
        
        Args:
            topic (str): MQTT topic
            payload_str (str): JSON payload string
        
        Returns:
            bool: Success status
        """
        if not self.connected:
            print("Database not connected")
            return False
            
        try:
            # Parse JSON payload
            payload = json.loads(payload_str)
            
            # Extract device ID from topic if not in payload
            if "device_id" not in payload and topic.startswith("Emotibit/"):
                device_parts = topic.split("/")
                if len(device_parts) >= 2:
                    payload["device_id"] = device_parts[1]
            
            # Add metadata
            document = {
                "topic": topic,
                "received_at": datetime.now(),
                **payload
            }
            
            # Insert into database
            result = await self.collection.insert_one(document)
            
            # Print debug info
            print(f"Saved data to database with ID: {result.inserted_id}")
            return True
            
        except json.JSONDecodeError:
            print(f"Invalid JSON payload: {payload_str}")
            return False
        except Exception as e:
            print(f"Error saving to database: {e}")
            return False
    
    # Keep synchronous version
    def save_sensor_data(self, topic, payload_str):
        """Save sensor data from MQTT message to database
        
        Args:
            topic (str): MQTT topic
            payload_str (str): JSON payload string
        
        Returns:
            bool: Success status
        """
        if not self.connected:
            print("Database not connected")
            return False
            
        try:
            # Parse JSON payload
            payload = json.loads(payload_str)
            
            # Extract device ID from topic if not in payload
            if "device_id" not in payload and topic.startswith("Emotibit/"):
                device_parts = topic.split("/")
                if len(device_parts) >= 2:
                    payload["device_id"] = device_parts[1]
            
            # Add metadata
            document = {
                "topic": topic,
                "received_at": datetime.now(),
                **payload
            }
            
            # Insert into database
            result = self.collection.insert_one(document)
            
            # Print debug info
            print(f"Saved data to database with ID: {result.inserted_id}")
            return True
            
        except json.JSONDecodeError:
            print(f"Invalid JSON payload: {payload_str}")
            return False
        except Exception as e:
            print(f"Error saving to database: {e}")
            return False
    
    async def save_device_status_async(self, device_id, status, timestamp):
        """Save device status to database asynchronously
        
        Args:
            device_id (str): Device ID
            status (str): Device status
            timestamp (int): Unix timestamp
        
        Returns:
            bool: Success status
        """
        if not self.connected:
            print("Database not connected")
            return False
            
        try:
            # Connect to the database
            status_collection = self.db["device_status"]

            # Check if there's an existing status record for this device
            existing_status = await status_collection.find_one(
                {"device_id": device_id}, 
                sort=[("timestamp", pymongo.DESCENDING)]
            )

            # If the device exists and has the same status, update the timestamp
            if existing_status and existing_status.get("status") == status:
                result = await status_collection.update_one(
                    {"_id": existing_status["_id"]},
                    {"$set": {
                        "timestamp": timestamp,
                        "datetime": datetime.fromtimestamp(timestamp),
                        "updated_at": datetime.now()
                    }}
                )
                print(f"Updated existing {status} status for device {device_id}")
                return True
            
            else:
                # Create new document for new status
                document = {
                    "device_id": device_id,
                    "status": status,
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp),
                    "created_at": datetime.now()
                }
                
                # Insert into database
                result = await status_collection.insert_one(document)
                print(f"Saved new device status to database with ID: {result.inserted_id}")
                return True
            
        except Exception as e:
            print(f"Error saving device status: {e}")
            return False
    
    # Keep synchronous version
    def save_device_status(self, device_id, status, timestamp):
        """Save device status to database
        
        Args:
            device_id (str): Device ID
            status (str): Device status
            timestamp (int): Unix timestamp
        
        Returns:
            bool: Success status
        """
        if not self.connected:
            print("Database not connected")
            return False
            
        try:
            # Connect to the database
            status_collection = self.db["device_status"]

            # Check if there's an existing status record for this device
            existing_status = status_collection.find_one(
                {"device_id": device_id}, 
                sort=[("timestamp", pymongo.DESCENDING)]
            )

            # If the device exists and has the same status, update the timestamp
            if existing_status and existing_status.get("status") == status:
                result = status_collection.update_one(
                    {"_id": existing_status["_id"]},
                    {"$set": {
                        "timestamp": timestamp,
                        "datetime": datetime.fromtimestamp(timestamp),
                        "updated_at": datetime.now()
                    }}
                )
                print(f"Updated existing {status} status for device {device_id}")
                return True
            
            else:
                # Create new document for new status
                document = {
                    "device_id": device_id,
                    "status": status,
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp),
                    "created_at": datetime.now()
                }
                
                # Insert into database
                result = status_collection.insert_one(document)
                print(f"Saved new device status to database with ID: {result.inserted_id}")
                return True
            
        except Exception as e:
            print(f"Error saving device status: {e}")
            return False