# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /var/www

# Copy the current directory contents into the container at /var/www
COPY . /var/www

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt


# Run uvicorn when the container launches
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]