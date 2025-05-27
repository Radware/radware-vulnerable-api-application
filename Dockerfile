# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Nginx and Supervisor
RUN apt-get update && apt-get install -y nginx supervisor

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install Flask Jinja2 requests "Werkzeug<2.3" python-json-logger

# Copy the backend and frontend code
COPY ./app /app/app
COPY ./frontend /app/frontend
COPY openapi.yaml /app/
COPY prepopulated_data.json /app/

# Configure Nginx as a reverse proxy
RUN rm /etc/nginx/sites-enabled/default
COPY nginx.conf /etc/nginx/sites-available/rapiv
RUN ln -s /etc/nginx/sites-available/rapiv /etc/nginx/sites-enabled/

# Setup supervisor to manage processes
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV PYTHONPATH=/app
# Default worker count can be overridden at runtime
ENV UVICORN_WORKERS=4

# Command to run supervisor, which will manage both services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
