# EmotiBit MQTT Data Pipeline

This repository contains a complete data pipeline for EmotiBit sensor data collection, processing, and analysis. The system consists of three main components:

- **MQTT Subscriber**: Collects and processes sensor data from EmotiBit devices.
- **EmotiBit Sensors API**: REST API for accessing and managing sensor data.
- **Model Classification API**: Machine learning API for analyzing sensor data.

---

## 📦 Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Jamessurapat26/emotibit-mqtt-data-pipeline.git
cd emotibit-mqtt-data-pipeline
````

### 2. Configure Environment Variables

Create or edit the following `.env` files as needed:

* `mqtt-subscriber/.env`
* `emotibit-sensors-api/.env`
* `model-classification-api/.env` (if applicable)

### 3. Build and Run with Docker Compose

```bash
docker-compose up --build -d
```

This command will:

* Build all services
* Create a MongoDB container for data storage
* Start all services in the background

---

## 🧱 Architecture

```plaintext
[EmotiBit Devices]
        |
        v
  [MQTT Broker (EMQX)]
        |
        v
[MQTT Subscriber Service]
        |
        v
    [MongoDB]
        |
        +---------------------+
        |                     |
        v                     v
[EmotiBit Sensors API]   [Model Classification API]
```

---

## 🛠 Services

### ✅ MQTT Subscriber (`mqtt-subscriber`)

* Connects to the EMQX public MQTT broker
* Listens for data from EmotiBit devices
* Processes and stores data in MongoDB
* Includes a data simulator for testing
* Internal only (no REST endpoints)

---

### ✅ EmotiBit Sensors API (`emotibit-sensors-api`)

* A [NestJS](https://nestjs.com/)-based REST API
* Provides endpoints to:

  * Retrieve sensor data
  * Manage device registrations
  * Perform basic analytics
* **URL**: `http://localhost:3000`

---

### ✅ Model Classification API (`model-classification-api`)

* A [FastAPI](https://fastapi.tiangolo.com/)-based ML API
* Provides endpoints to:

  * Classify incoming sensor data
  * Predict outcomes using trained models
* **URL**: `http://localhost:8000`

---

## 🔬 Development & Testing

### ✅ Testing with the built-in simulator

The MQTT Subscriber includes a test publisher that simulates EmotiBit device data.

### ➕ Adding your own device

1. Update the topics in `mqtt_handle.py`
2. Restart the MQTT Subscriber service:

```bash
docker-compose restart mqtt-subscriber
```

---

## 🧰 Troubleshooting

### ❌ Connection Issues

* Verify MongoDB URI in `docker-compose.yml` is correct
* Check that the MQTT broker `broker.emqx.io` is accessible from your network

### ❌ Data Flow Issues

* Check logs with:

```bash
docker-compose logs -f
```

* Verify topic names and message structure in your MQTT config

