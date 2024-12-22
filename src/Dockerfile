# Use the official Golang image as the base image
FROM golang:latest

# Install basic C tools and cJSON library
RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get install -y libcjson-dev

# Set the working directory inside the container
WORKDIR /app

# Copy the entire backend project into the container
COPY ./back .

# Build the Go project
RUN go build -o backend.o .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the executable
CMD ["./backend.o"]