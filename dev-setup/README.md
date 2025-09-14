# Bazarr Development Environment

A complete Docker-based development environment for Bazarr with live code reloading for both backend and frontend.

> **Note**: This is the official Docker development setup for Bazarr. All Docker-related files are centralized here to avoid confusion and ensure consistency.

## Quick Start

### 1. Clone your fork
```bash
git clone https://github.com/YOUR_USERNAME/bazarr.git
cd bazarr/dev-setup
```

### 2. Run the setup script
```bash
./setup-dev.sh
```
This will create the necessary directories, config files, and setup both Bazarr and Autopulse for development.

### 3. Start development environment
```bash
# Start Bazarr only
docker compose up --build

# Or start with Autopulse for Plex integration testing
docker compose --profile autopulse up --build
```

### 4. Access applications
**🌐 Open your browser to: http://localhost:5173**

This is the Bazarr web interface with live reloading. The frontend automatically communicates with the backend API (port 6767).

**Default credentials:**
- **Bazarr**: Username: `admin`, Password: `admin`
- **Autopulse**: Username: `admin`, Password: `password`
- API Key: `bazarr` (for API access)

**Important**: 
- Port 5173: Frontend development server with hot module replacement
- Port 6767: Backend API server (not meant for direct browser access)
- Port 2875: Autopulse service (when enabled with `--profile autopulse`)

## What This Provides

### 🐳 **Fully Containerized Development**
- Separate optimized containers for backend (Python/Alpine) and frontend (Node.js)
- No need for local Node.js, Python, or other dependencies on your host
- Consistent development environment across different machines
- Each container only includes necessary dependencies

### 🔄 **Live Code Reloading**
- **Backend**: Python files are mounted and changes reflect immediately
- **Frontend**: Full frontend directory mounted with Vite hot module replacement
- **Libraries**: Both custom_libs and libs are mounted for modification

### 📁 **Volume Mounts**
```
../bazarr         → /app/bazarr/bin/bazarr       (Backend source)
../frontend       → /app/bazarr/bin/frontend     (Frontend source)
../custom_libs    → /app/bazarr/bin/custom_libs  (Custom libraries)
../libs           → /app/bazarr/bin/libs         (Third-party libraries)
./data            → /app/bazarr/data             (Persistent data)
./autopulse       → /app/data                    (Autopulse data - when enabled)
```

### 🌐 **Port Configuration**
- **5173**: Vite development server with hot reloading
- **6767**: Bazarr backend API and web interface
- **2875**: Autopulse service (when enabled)

## Development Workflow

### Making Changes

1. **Backend Development**:
   - Edit files in `../bazarr/` directory
   - Changes are immediately available in the running container
   - No restart needed for most Python changes

2. **Frontend Development**:
   - Edit files in `../frontend/` directory
   - Vite automatically reloads the browser
   - Install new npm packages by rebuilding: `docker compose up --build`

3. **Adding Dependencies**:
   - **Python**: Add to `../requirements.txt` and rebuild
   - **Node.js**: Add to `../frontend/package.json` and rebuild

### Useful Commands

```bash
# Start development environment
docker compose up

# Start in background (detached)
docker compose up -d

# Start with optional Autopulse service for Plex integration testing
docker compose --profile autopulse up -d

# Rebuild after dependency changes
docker compose up --build

# View logs
docker compose logs -f

# Access backend container shell for debugging
docker compose exec bazarr-backend sh

# Access frontend container shell for debugging  
docker compose exec bazarr-frontend sh

# Stop the environment
docker compose down

# Complete cleanup (removes containers, networks, volumes)
docker compose down -v
```

### Autopulse Setup (Optional)

To include Autopulse for testing Plex integration features:

```bash
# Setup development environment with Autopulse support
./setup-dev.sh --autopulse

# Start with Autopulse enabled
docker compose --profile autopulse up --build
```

## Environment Configuration

The development environment includes these settings:

```bash
NODE_ENV=development
VITE_PROXY_URL=http://127.0.0.1:6767
VITE_BAZARR_CONFIG_FILE=/app/bazarr/data/config/config.yaml
VITE_CAN_UPDATE=true
VITE_HAS_UPDATE=false
VITE_REACT_QUERY_DEVTOOLS=true
```

## Data Persistence

Configuration and data are persisted in local directories:

**Bazarr:**
- `./data/config/` - Bazarr configuration files
- `./data/cache/` - Application cache
- `./data/log/` - Application logs
- `./data/db/` - Database files

**Autopulse (when enabled):**
- `./autopulse/config.yaml` - Autopulse configuration
- `./autopulse/data/` - Autopulse database and data

## Troubleshooting

### Port Conflicts
If ports 5173, 6767, or 2875 are already in use:
```bash
# Check what's using the ports
lsof -i :5173
lsof -i :6767
lsof -i :2875

# Either stop those services or modify ports in docker-compose.yml
```

### Permission Issues
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER ./data ./autopulse
```

### Frontend Not Loading
- Check frontend logs: `docker compose logs -f bazarr-frontend`
- Ensure Vite dev server started successfully
- Try rebuilding frontend: `docker compose up --build bazarr-frontend`

### Backend API Issues
- Verify backend is running: `docker compose logs bazarr-backend`

### Authentication/Login Issues
If you're prompted for a password:
1. The default credentials for Bazarr are: **admin/admin**
2. The default credentials for Autopulse are: **admin/password**
3. Check if `data/config/config.yaml` exists with proper auth settings
4. If not, run `./setup-dev.sh` to create the proper config
5. Restart the containers: `docker compose restart`
6. The API key is set to: **bazarr**

If you still have issues:
- Delete the data directory: `rm -rf data/`
- Run the setup script: `./setup-dev.sh`
- Rebuild and start: `docker compose up --build`
- Check if port 6767 is accessible: `curl http://localhost:6767`
- Review Python error logs in the backend container output

### Complete Reset
If you encounter persistent issues:
```bash
# Stop and remove everything
docker compose down -v

# Remove built images
docker rmi dev-setup-bazarr-backend dev-setup-bazarr-frontend

# Clean up data directories (optional - will lose all data)
rm -rf data/ autopulse/

# Recreate setup
./setup-dev.sh

# Rebuild from scratch
docker compose up --build
```

## Optional Services

### 🔗 **Autopulse Integration**
For testing Plex integration and webhook features, you can optionally enable the Autopulse service:

```bash
# Start with Autopulse for Plex metadata refresh testing
docker compose --profile autopulse up --build

# Access Autopulse web interface
open http://localhost:2875
```

**Autopulse Features:**
- **Dynamic Configuration Generation**: Bazarr can generate Autopulse configurations automatically using the template API
- **Path Rewrite Detection**: Smart detection of mount point differences between Bazarr and Plex
- **Webhook Testing**: Test subtitle download webhooks that trigger Plex metadata refreshes

**Usage with Bazarr:**
1. Configure Plex settings in Bazarr (OAuth authentication recommended)
2. Navigate to the Plex settings page in Bazarr
3. Use the "Generate Autopulse Configuration" feature to create an optimized config
4. Save the generated configuration as `config.toml` in your Autopulse container
5. Configure external webhooks to point to `http://autopulse:2875/triggers/bazarr`

**Testing the Integration:**
1. Set up a Plex server with OAuth in Bazarr
2. Generate an Autopulse configuration in the Plex settings
3. Enable external webhooks pointing to Autopulse
4. Download subtitles and verify Autopulse receives webhook calls

## Development Tips

### Container Shell Access
```bash
# Access the backend container
docker compose exec bazarr-backend sh

# Access the frontend container
docker compose exec bazarr-frontend sh

# Install additional tools inside backend container if needed
docker compose exec bazarr-backend apk add --no-cache curl vim

# Install additional tools inside frontend container if needed
docker compose exec bazarr-frontend apk add --no-cache curl vim
```

### Logs and Debugging
```bash
# Follow all logs
docker compose logs -f

# Follow only backend logs
docker compose logs -f bazarr-backend

# Follow only frontend logs  
docker compose logs -f bazarr-frontend
```

### Performance
- Separate containers for frontend and backend for better resource utilization
- Backend uses lightweight Alpine Linux with Python
- Frontend uses optimized Node.js Alpine image
- All file changes are immediately reflected due to volume mounts

## Architecture

```
Host Machine
├── bazarr/ (your code)
│   ├── bazarr/ → mounted in backend container
│   ├── frontend/ → mounted in frontend container  
│   ├── custom_libs/ → mounted in backend container
│   └── libs/ → mounted in backend container
└── dev-setup/ (all dev environment files in one place)
    ├── data/ → persistent Bazarr data
    ├── autopulse/ → persistent Autopulse data (when enabled)
    ├── Dockerfile.backend → Python/Alpine backend image
    ├── Dockerfile.frontend → Node.js frontend image (dev-optimized)
    ├── docker-compose.yml → Orchestration config
    ├── setup-dev.sh → Development environment setup script
    └── README.md

Backend Container (/app/bazarr/bin/)
├── bazarr/ (backend source - mounted)
├── custom_libs/ (mounted)
├── libs/ (mounted)
└── data/ (persistent data - mounted)

Frontend Container (/app/)
├── src/ (frontend source - mounted)
├── public/ (static assets - mounted)
├── config/ (configuration - mounted)
└── node_modules/ (npm packages - container only)

Autopulse Container (/app/)
├── config.yaml (configuration - mounted)
└── data/ (persistent data - mounted)
```

## Next Steps

1. Start developing - all changes are live!
2. Test your modifications at http://localhost:6767 and http://localhost:5173
3. Submit pull requests to the main repository

Happy coding! 🚀
