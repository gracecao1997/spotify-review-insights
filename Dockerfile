FROM python:3.12-slim
WORKDIR /app
COPY core.py stages.py dashboard.py ./
COPY web/dashboard.html ./web/dashboard.html
# Supply a prepared read-only database in deployment/ before building.
COPY deployment/dashboard.sqlite ./deployment/dashboard.sqlite
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "python dashboard.py --db deployment/dashboard.sqlite --host 0.0.0.0 --port ${PORT} --serve"]
