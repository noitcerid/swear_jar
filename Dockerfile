# 1. Use an official Python runtime as a parent image
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your application's code into the container
COPY . .

# 5. Make port 5000 available to the world outside this container
EXPOSE 5000

# 6. Command to run the application using Gunicorn
# This is a more robust server than the default Flask development server.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "swear_jar_web:app"]
