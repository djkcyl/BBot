FROM python:3.9.15-slim
WORKDIR /bbot
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV PLAYWRIGHT_BROWSERS_PATH "static/browser"
RUN playwright install --with-deps chromium
COPY . .
VOLUME /bbot/data
EXPOSE 6080
CMD ["python", "main.py"]