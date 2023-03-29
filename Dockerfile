FROM python:3.9.15-slim
WORKDIR /bbot
RUN --mount=type=tmpfs,target=/var/cache/apt/archives \
    --mount=type=tmpfs,target=/var/lib/apt/lists \
    --mount=type=tmpfs,target=/tmp \
    apt update && apt install -y gcc
COPY requirements.txt .
RUN --mount=type=tmpfs,target=/tmp \
    pip install --no-cache-dir -r requirements.txt
ENV PLAYWRIGHT_BROWSERS_PATH "aunly_bbot/static/browser"
RUN --mount=type=tmpfs,target=/var/cache/apt/archives \
    --mount=type=tmpfs,target=/var/lib/apt/lists \
    --mount=type=tmpfs,target=/tmp \
    sed -i 's/main/main non-free/g' /etc/apt/sources.list && \
    python -m playwright install --with-deps firefox
COPY . .
VOLUME /bbot/data
EXPOSE 6080
CMD ["python", "main.py"]
