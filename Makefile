# Description: Makefile for the project

# Default target
init: env install

# Install requirements and ffmpeg
install: install/requirements install/ffmpeg

# Install requirements
install/requirements:
	pip install -r requirements.txt

# Install ffmpeg
install/ffmpeg:
	brew install ffmpeg

# Virtual environment
env: env/init env/activate

# Create virtual environment
env/init:
	python3 -m venv venv

# Activate virtual environment
env/activate:
	. venv/bin/activate

server: env/activate
    # Run server
	python3 server/main.py

client: env/activate
    # Run client
	python3 client/main.py