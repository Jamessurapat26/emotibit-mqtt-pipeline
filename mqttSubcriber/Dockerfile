FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Environment variables (these can be overridden at runtime)
ENV MONGO_URI="mongodb+srv://surapat:surapat26@learnmongo.zh9l7.mongodb.net/?retryWrites=true&w=majority&appName=Learnmongo"
ENV MONGO_DB_NAME="emotibit_data"
ENV MONGO_COLLECTION="sensor_readings"

# MONGO_URI = "mongodb://localhost:27017/"
# MONGO_DB_NAME = "emotibit_data"
# MONGO_COLLECTION = "sensor_readings"

# Run the application
CMD ["bash", "-c", "python main.py & python ./test/testpublish.py & wait"]