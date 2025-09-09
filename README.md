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
- `.github/workflows/ghcr.yml` GitHub Actions to build and push images to GHCR (latest tag only)

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

## Deploy to a remote server (Docker Swarm)
Two ways to get this stack running on a remote Linux server:

1) Build on the remote (simple, no registry)
- Prereqs on the server: Docker Engine installed and user in the `docker` group; inbound TCP 8080 open.
- On the server:

```bash
# init swarm (single node)
sudo docker swarm init

# clone/copy the repo to the server
cd /opt && sudo git clone <your-repo-url> webfile && cd webfile

# build images on the server
sudo docker build -t webfile-backend:latest -f backend/Dockerfile .
sudo docker build -t webfile-frontend:latest -f frontend/Dockerfile .
sudo docker build -t webfile-nginx:latest -f nginx/Dockerfile .

# deploy stack
sudo docker stack deploy -c docker-compose.yml webfile

# watch status
sudo docker stack services webfile
```

2) Deploy from GHCR (recommended for CI/CD)
- The workflow publishes:
  - ghcr.io/<OWNER>/webfile-backend:latest
  - ghcr.io/<OWNER>/webfile-frontend:latest
  - ghcr.io/<OWNER>/webfile-nginx:latest

On the remote server (bash):

```bash
# init swarm if not already
sudo docker swarm init

# login to GHCR (PAT needs at least read:packages)
echo <PAT> | sudo docker login ghcr.io -u <GITHUB_USERNAME> --password-stdin

# set env for compose substitution (use latest)
export REGISTRY="ghcr.io/<OWNER>"
export TAG="latest"

# obtain the repo on server
cd /opt && sudo git clone <your-repo-url> webfile || true
cd /opt/webfile

# IMPORTANT: use only the remote stack file (no build keys) and preserve env with sudo
sudo --preserve-env=REGISTRY,TAG docker stack deploy -c stack.remote.yml webfile

sudo docker stack services webfile
```

Upgrade/Rollback
- New commits to main produce new latest images; re-run the deploy command to pull and update.
- For immutable versioned tags, adjust the workflow and set TAG accordingly.

Ports & firewall
- Ensure TCP 8080 is open on the server’s firewall to access Nginx.
- For multi-node swarms, also allow 2377/tcp (manager), 7946/tcp+udp and 4789/udp for overlay networking.

Multi-node storage note
- This stack uses a local volume `data` attached to the backend container. In a multi-node swarm, use shared storage (NFS/SMB/Cloud) or pin the backend to a node with a placement constraint.
