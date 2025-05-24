# Use Python 3.11 to support newer package versions
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for some Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Create staticfiles directory
RUN mkdir -p staticfiles

# Expose the port your app runs on
EXPOSE 8080

# Command to run your application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
