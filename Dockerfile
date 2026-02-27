# Use slim Python image for smaller size
FROM python:3.12-slim

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock* ./

# Install uv and dependencies
RUN pip install uv && uv sync --frozen

# Install self package
RUN pip install -e .

# Copy project files
COPY . .

# Default command
ENTRYPOINT ["orion"]