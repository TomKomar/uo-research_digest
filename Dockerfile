# Use the official Python image from the Docker Hub
FROM python:3.9-slim
# Copy the requirements file into the container
COPY requirements.txt .
# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the environment variable for the timezone
ENV TZ=UTC

# Run the main.py script on container startup
CMD ["python", "/app/main.py"]