from schema.predictSchema import PredictionOutput  # Updated class name
from fastapi import APIRouter, HTTPException
from typing import List
import random
import time
from preprocess.preprocess import Preprocessor  # Assuming this is a function to read the pickle file
from tensorflow.keras.models import load_model
from pydantic import BaseModel
import pandas as pd
import numpy as np
import neurokit2 as nk
import json

model = load_model("assets/stress_model.keras")

router = APIRouter()

# Define your input schema
class InputData(BaseModel):
    EDA_Phasic: float
    SCR_Amplitude: float
    NumPeaks: float
    HRV_SDNN: float
    HRV_RMSSD: float
    HRV_LFHF: float
    PPG_Rate: float
    HRV_SD1: float
    HRV_SD2: float
    HRV_SD1SD2: float
    HRV_DFA_alpha1: float
    HRV_SampEn: float
    HRV_ApEn: float
    gender: int
    bmi: float
    bmi_category: int
    sleep: int
    type: int


@router.get("/{deviceId}", response_model=PredictionOutput)  # Change to "/" since prefix is added in main.py
async def predict(deviceId: str):

    randomHeartRate = random.randint(60, 100)  # Simulate heart rate
    randomHeartRate = round(randomHeartRate)

    randomStressPrediction = random.choice(["normal", "low", "medium", "high"])
    timestamp = int(time.time())  # Get current timestamp

    data = preprocess.read_pkl()  # Assuming this function reads the pickle file and returns the data
    print(data)

    jsonData = {
        "deviceId": deviceId,
        "stressPrediction": randomStressPrediction,
        "heartRate": randomHeartRate,
        "timeStamp": timestamp
    }

    return jsonData

@router.post("/")
def predict_stress(data: InputData):
    # Convert input to DataFrame
    input_df = pd.DataFrame([data.dict()])
    
    # Predict using the model
    prediction = model.predict(input_df.to_numpy())
    
    # For multi-class classification
    predicted_class = int(np.argmax(prediction, axis=1)[0])
    
    return {"predicted_stress": predicted_class}

@router.get("/test/{deviceId}")
async def test_predict(deviceId: str):
    # Create an instance with the deviceId
    processor = Preprocessor(deviceId)
    # Then call the method on that instance
    data = await processor.fetch_recent_data()

    merged_data = {
        "deviceId": deviceId,
        "eda": [],
        "ppg": [],
        "timestamps": []
    }

    for doc in data:
        if 'sensors' in doc and 'eda' in doc['sensors']:
            merged_data['eda'].extend(doc['sensors']['eda'])
        
        if 'sensors' in doc and 'ppg' in doc['sensors']:
            merged_data['ppg'].extend(doc['sensors']['ppg'])
            
        if 'timestamp' in doc:
            merged_data['timestamps'].append(doc['timestamp'])
    
    if merged_data['ppg']:
        print(f"PPG data sample (first 10 values): {merged_data['ppg'][:10]}")

    ppg = merged_data['ppg']
    eda = merged_data['eda']

    ppg_signals, _ = nk.ppg_process(ppg, sampling_rate=100, heart_rate=True)
    print(f"PPG signals: {ppg_signals}")

    eda_signals, _ = nk.eda_process(eda, sampling_rate=15)
    print(f"EDA signals: {eda_signals}")

    ppg_peak = ppg_signals['PPG_Peaks']
    hrv_indices = nk.hrv(ppg_peak, sampling_rate=100)
    print(f"HRV indices: {hrv_indices}")

      # Merge the dataframes
    resampled_ppg = ppg_signals.tail(100)
    resampled_ppg = resampled_ppg.mean()
    
    resampled_eda = eda_signals.tail(15)
    resampled_eda = resampled_eda.mean()
    print(f"PPG signals after resampling: {resampled_ppg}")
    print(f"EDA signals after resampling: {resampled_eda}")

    # Pack the data into a JSON-serializable format
    processed_data = {
        "deviceId": deviceId,
        "eda_features": {k: None if pd.isna(v) else v for k, v in resampled_eda.to_dict().items()},
        "ppg_features": {k: None if pd.isna(v) else v for k, v in resampled_ppg.to_dict().items()},
        "hrv_indices": {k: None if pd.isna(v) else v for k, v in (hrv_indices.iloc[0].to_dict() if not hrv_indices.empty else {}).items()},
        "timestamp": int(time.time())
    }

    print(f"Processed data: {processed_data}")

    try:
        db_result = await processor.save_preprocessed_data(processed_data)
        if "inserted_id" in db_result:
            # Convert MongoDB ObjectId to string before returning
            processed_data["db_status"] = "success"
            processed_data["inserted_id"] = str(db_result["inserted_id"])
        else:
            processed_data["db_status"] = "error"
            processed_data["error"] = db_result.get("error")
    except Exception as e:
        processed_data["db_status"] = "error"
        processed_data["error"] = str(e)
        
    try:
        json_data = json.dumps({
            "status": "success",
            "data": processed_data,
            "db_result": db_result
        }, default=str)  # default=str will convert any non-serializable objects to strings
        
        return json.loads(json_data)
    except Exception as e:
        print(f"Error serializing response: {e}")
        return {
            "status": "error",
            "message": "Failed to serialize response",
            "error": str(e)
        }