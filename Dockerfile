# Python 3.10 slim image (lightweight)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY .env .env
# Copy latest_event.json if it exists (optional, mostly for local dev)
# In production, this file is created at runtime.

# Install dependencies
RUN uv sync --frozen

# Command to run the bot
# Use standard scheduling mode
CMD ["uv", "run", "src/final_fantasy_eventbot/main.py"]
