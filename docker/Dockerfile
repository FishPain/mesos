FROM python:3.9

# Set environment variables
ENV PYTHONUNBUFFERED 1

# use tsinghua pip mirror if server is running in China 
# if not can comment out this line and pip will use the default
# pip mirror
# ENV PIP_INDEX_URL https://pypi.tuna.tsinghua.edu.cn/simple

# tells Flask to look for an application instance named app in the server module 
ENV FLASK_APP server:app

# Set working directory
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt /app/
COPY /libs/ /app/libs/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["python", "server.py"]
