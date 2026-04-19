FROM python:3.13-slim
WORKDIR /usr/local/app

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.11.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy in the source code
COPY . .
EXPOSE 8000

# Pre-download the embedding model at build time (as root) so no
# permission issues or cold-start downloads occur at runtime
ENV HF_HOME=/opt/hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nomic-ai/nomic-embed-text-v1', trust_remote_code=True)"

# Setup an app user so the container doesn't run as the root user
RUN useradd -m app && chown -R app:app /opt/hf_cache
USER app

CMD ["python", "main.py"]