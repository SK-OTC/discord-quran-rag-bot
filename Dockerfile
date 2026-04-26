FROM python:3.13-slim
WORKDIR /usr/local/app

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.4.0+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Pre-create cache directory and download model BEFORE copying source code
# This way code changes don't bust the model download cache layer
ENV HF_HOME=/opt/hf_cache
RUN mkdir -p /opt/hf_cache && chmod 777 /opt/hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nomic-ai/nomic-embed-text-v1', trust_remote_code=True)"

# Setup app user AFTER model download
RUN useradd -m app && chown -R app:app /opt/hf_cache /usr/local/app

# Copy source code LAST so code changes don't trigger model re-download
COPY . .
EXPOSE 8000

USER app
CMD ["python", "main.py"]