FROM python:3.9

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=server:app

# Set working directory
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg

# Copy requirements.txt to the working directory
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --retries 3 --timeout 60 -r requirements.txt 

# Clean up the pip cache to reduce image size
RUN rm -rf /root/.cache/pip

# Copy the current directory contents into the container at /app
COPY . /app/

# Copy supervisord configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
