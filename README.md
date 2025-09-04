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

2) Push to GitHub Container Registry (GHCR), then deploy (recommended for CI/CD)
- You’ll need a GitHub Personal Access Token (PAT):
  - Classic PAT scopes: `write:packages`, `read:packages` (and optionally `delete:packages`)
  - Or a fine-grained PAT with Packages: Read/Write on your org/user
- Images will be published to `ghcr.io/<OWNER>` where `<OWNER>` is your GitHub username or org.

From your workstation (PowerShell):

```powershell
# login to GHCR (create a PAT, then paste it when prompted)
docker login ghcr.io -u <GITHUB_USERNAME>

# set owner namespace and a tag
$env:OWNER = "<GITHUB_USERNAME_OR_ORG>"
$env:REGISTRY = "ghcr.io/$env:OWNER"
$env:TAG = "1.0.0"

# build local images
docker build -t webfile-backend:latest -f backend/Dockerfile .
docker build -t webfile-frontend:latest -f frontend/Dockerfile .
docker build -t webfile-nginx:latest -f nginx/Dockerfile .

# tag for GHCR
docker tag webfile-backend:latest  $env:REGISTRY/webfile-backend:$env:TAG
docker tag webfile-frontend:latest $env:REGISTRY/webfile-frontend:$env:TAG
docker tag webfile-nginx:latest    $env:REGISTRY/webfile-nginx:$env:TAG

# push to GHCR
docker push $env:REGISTRY/webfile-backend:$env:TAG
docker push $env:REGISTRY/webfile-frontend:$env:TAG
docker push $env:REGISTRY/webfile-nginx:$env:TAG
```

On the remote server (bash):

```bash
# init swarm if not already
sudo docker swarm init

# login to GHCR (PAT needs at least read:packages)
echo <PAT> | sudo docker login ghcr.io -u <GITHUB_USERNAME> --password-stdin

# set env for compose variable substitution
export REGISTRY="ghcr.io/<GITHUB_USERNAME_OR_ORG>"
export TAG="1.0.0"

# obtain the repo on server
cd /opt && sudo git clone <your-repo-url> webfile || true
cd /opt/webfile

# deploy merging the override to use GHCR images
sudo docker stack deploy -c docker-compose.yml -c stack.remote.yml webfile

sudo docker stack services webfile
```

Upgrade/Rollback
- Push a new tag to GHCR and redeploy with the new `TAG`. Swarm will roll your services.
- To roll back, redeploy with the previous `TAG`.

Ports & firewall
- Ensure TCP 8080 is open on the server’s firewall to access Nginx.
- For multi-node swarms, also allow 2377/tcp (manager), 7946/tcp+udp and 4789/udp for overlay networking.

Multi-node storage note
- This stack uses a local volume `data` attached to the backend container. In a multi-node swarm, use shared storage (NFS/SMB/Cloud) or pin the backend to a node with a placement constraint.
