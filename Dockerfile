# Python 3.10 slim image (lightweight)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src
# .env is handled by Railway Variables, do not copy it.

# Install dependencies
RUN uv sync --frozen

# Command to run the bot
# Use standard scheduling mode
CMD ["uv", "run", "src/final_fantasy_eventbot/main.py"]
