# WebFile

Simple intranet file server with Flask frontend and backend, proxied by Nginx. Runs in Docker Swarm. Files are persisted in a volume and listed for browsing, uploading (files or folders), and direct downloads via stable URIs.

## Features
- Backend Flask API exposing:
  - List directory (GET /api/list?path=<rel>)
  - Create folder (POST /api/mkdir JSON: {"path": "sub/dir"})
  - Upload file(s) (POST /api/upload?path=<rel>, multipart field `file`, supports multiple)
  - Direct download (GET /download/<path>) stable per-file URI
- Frontend Flask UI for browsing and actions
- Gunicorn serving both Flask apps
- Nginx reverse proxy
- Docker Swarm orchestration with a shared volume for data

## Structure
- `backend/` Flask API and Dockerfile
- `frontend/` Flask UI and Dockerfile
- `nginx/` Nginx config and Dockerfile
- `docker-compose.yml` Swarm stack file
- `data/` local data folder (for dev, mapped into volume in Swarm)

## Run (Docker Swarm)
Initialize Swarm if needed and deploy the stack.

```powershell
# 1) Initialize swarm (only once per machine)
docker swarm init

# 2) Build images
docker build -t webfile-backend:latest -f backend/Dockerfile .
docker build -t webfile-frontend:latest -f frontend/Dockerfile .
docker build -t webfile-nginx:latest -f nginx/Dockerfile .

# 3) Deploy stack
docker stack deploy -c docker-compose.yml webfile

# 4) Check services
docker stack services webfile

# 5) Open the app (Nginx proxy)
Start-Process http://localhost:8080/
```

To remove:

```powershell
docker stack rm webfile
```

## Notes
- Volume `data` persists uploads. On Swarm, it's a local driver volume on the node where the backend runs.
- Frontend folder upload uses the `webkitdirectory` attribute, supported by Chromium-based browsers.
- For HTTPS, terminate TLS at Nginx (extend the image with certs and listen 443).
