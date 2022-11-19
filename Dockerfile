FROM python:3.9.15-slim
WORKDIR /bbot
RUN --mount=type=tmpfs,target=/var/cache/apt/archives \
    --mount=type=tmpfs,target=/var/lib/apt/lists \
    apt update && apt install -y gcc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV PLAYWRIGHT_BROWSERS_PATH "static/browser"
RUN --mount=type=tmpfs,target=/var/cache/apt/archives \
    --mount=type=tmpfs,target=/var/lib/apt/lists \
    sed -i 's/main/main non-free/g' /etc/apt/sources.list && \
    playwright install --with-deps chromium
COPY . .
VOLUME /bbot/data
EXPOSE 6080
CMD ["python", "main.py"]