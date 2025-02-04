FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Expose a port if required (optional)
# EXPOSE 8080

# Set the command to run the bot
CMD ["python", "bot.py"]