FROM python:3.13-slim
WORKDIR /usr/local/app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt
    
ENV HF_HOME=/opt/hf_cache
RUN mkdir -p /opt/hf_cache && chmod 777 /opt/hf_cache
RUN useradd -m app && chown -R app:app /opt/hf_cache /usr/local/app

COPY . .
EXPOSE 8000

USER app
CMD ["python", "main.py"]