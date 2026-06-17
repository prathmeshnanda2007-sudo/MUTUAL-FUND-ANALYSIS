import multiprocessing

# Bind to 127.0.0.1 (localhost) on port 8000, since Nginx will act as the reverse proxy
bind = "127.0.0.1:8000"

# Use Uvicorn's worker class for ASGI apps (FastAPI)
worker_class = "uvicorn.workers.UvicornWorker"

# Formula for number of workers: (2 x $num_cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Timeout and keepalive
timeout = 120
keepalive = 5

# Logging configuration
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Application reloading (only use True in development)
reload = False

# Worker lifecycle
max_requests = 1000
max_requests_jitter = 50
