# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your python files and .env into the container
COPY . .

# Expose the port the Gateway API runs on
EXPOSE 8000

# By default, run the Gateway API
CMD ["uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8000"]