# Use the Playwright Python image as the base
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Set working directory inside the container
WORKDIR /app

# Copy your application code into the container
# This assumes your FastAPI application is in the /app directory of your project
COPY . /app

# Install Python dependencies from your requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your FastAPI application runs on (default is 8000)
EXPOSE 8000

# Command to run your FastAPI application with Uvicorn
# Make sure to replace 'app.main:app' with the actual path to your FastAPI app instance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 