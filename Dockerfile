# 1️⃣ Base image (Python runtime)
FROM python:3.11-slim

# 2️⃣ Set working directory inside container
WORKDIR /app

# 3️⃣ Copy dependency list first (for caching)
COPY requirements.txt .

# 4️⃣ Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copy application code
COPY service ./service

# 6️⃣ Tell Python where to find packages
ENV PYTHONPATH=service

# 7️⃣ Expose API port
EXPOSE 8000

# 8️⃣ Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]