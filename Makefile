# Description: Makefile for the project

# Default target
init: venv install

# Install requirements and ffmpeg
install: install/requirements install/ffmpeg

# Install requirements
install/requirements:
	pip install -r requirements.txt

# Install ffmpeg
install/ffmpeg:
	brew install ffmpeg

# Virtual environment
venv: venv/init venv/activate

# Create virtual environment
venv/init:
	python3 -m venv venv

# Activate virtual environment
venv/activate:
	source venv/bin/activate

server: venv/activate
    # Run server
	python3 server/server.py

client: venv/activate
    # Run client
	python3 client/client.py