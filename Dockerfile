# 1. Base Image (Python 3.11 slim version)
FROM python:3.11-slim

# 2. Working Directory 
WORKDIR /app

ENV PYTHONUNBUFFERED=1

# 3. System dependencies install karein (Agar zaroorat ho)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Pehle requirements.txt copy karein (Caching ke liye)
COPY requirements.txt .

# 5. Dependencies install karein
RUN pip install --no-cache-dir -r requirements.txt

# 6. Baaki ka code copy karein
COPY . .

# 7. Port expose karein
EXPOSE 8000

# 8. Server run karein
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]