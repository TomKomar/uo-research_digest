# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the environment variable for the timezone
ENV TZ=UTC

# Run the main.py script on container startup
CMD ["python", "/app/main.py"]