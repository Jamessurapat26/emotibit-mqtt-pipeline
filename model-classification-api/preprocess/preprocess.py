import os
import pickle
import time
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

# --- MongoDB Config ---
MONGO_DETAILS = "mongodb+srv://surapat:surapat26@learnmongo.zh9l7.mongodb.net/?retryWrites=true&w=majority&appName=Learnmongo"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client["emotibit_data"]
collection = database["sensor_readings"]

# --- Preprocess Class ---
class Preprocessor:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.encoder = self.load_encoder()

    def load_encoder(self):
        """Load the pickle encoder."""
        try:
            current_dir = Path(__file__).resolve().parent
            file_path = current_dir.parent / "assets" / "label.pkl"
            with open(file_path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            print(f"❌ Encoder file not found at {file_path}")
        except Exception as e:
            print(f"❌ Failed to load encoder: {e}")
        return None
        
    def fix_mongo_id(self, doc):
        """Convert MongoDB _id to string"""
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc
        
    async def fetch_recent_data(self, minutes: int = 6, projection=None):
        try:
            time_threshold = int(time.time()) - (minutes * 60)
            
            # Default projection to only fetch fields we need if not specified
            if projection is None:
                projection = {
                    "device_id": 1, 
                    "timestamp": 1, 
                    "sensors.eda": 1, 
                    "sensors.ppg": 1
                }
                    
            # Create query with optimized index fields first
            query = {
                "device_id": self.device_id,
                "timestamp": {"$gte": time_threshold}
            }
            
            # Use projection to limit returned fields
            # Remove the hint() until the index is created
            cursor = collection.find(
                query, 
                projection
            ).sort("timestamp", 1)
            
            # Set batch size for more efficient data transfer
            cursor.batch_size(100)
            
            raw_data = await cursor.to_list(length=None)
            if not raw_data:
                print(f"⚠️ No data found for device {self.device_id} in the last {minutes} minutes.")
                return []  # Return empty list instead of None for consistent behavior

            # Convert _id to string in all documents
            fixed_data = [self.fix_mongo_id(doc) for doc in raw_data]
            return fixed_data

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []  # Return empty list for consistent behavior
        
    async def save_preprocessed_data(self, data):
        collection = database["preprocessed_data"]
        try:
            # Insert the preprocessed data into the collection
            result = await collection.insert_one(data)
            print(f"✅ Preprocessed data saved with id: {result.inserted_id}")
        except Exception as e:
            print(f"❌ Error saving preprocessed data: {e}")