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
./test-setup.sh
```
This will create the necessary directories and a minimal config file with default credentials for development.

### 3. Start development environment
```bash
docker compose up --build
```

### 4. Access applications
**🌐 Open your browser to: http://localhost:5173**

This is the Bazarr web interface with live reloading. The frontend automatically communicates with the backend API (port 6767).

**Default credentials:**
- Username: `admin`
- Password: `admin`

**Important**: 
- Port 5173: Frontend development server with hot module replacement
- Port 6767: Backend API server (not meant for direct browser access)
- API Key: `bazarr` (for API access)

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
```

### 🌐 **Port Configuration**
- **6767**: Bazarr backend API and web interface
- **5173**: Vite development server with hot reloading

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

Configuration and data are persisted in the `./data` directory:
- `./data/config/` - Bazarr configuration files
- `./data/cache/` - Application cache
- `./data/log/` - Application logs

## Troubleshooting

### Port Conflicts
If ports 6767 or 5173 are already in use:
```bash
# Check what's using the ports
lsof -i :6767
lsof -i :5173

# Either stop those services or modify ports in docker-compose.yml
```

### Permission Issues
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER ./data
```

### Frontend Not Loading
- Check frontend logs: `docker compose logs -f bazarr-frontend`
- Ensure Vite dev server started successfully
- Try rebuilding frontend: `docker compose up --build bazarr-frontend`

### Backend API Issues
- Verify backend is running: `docker compose logs bazarr-backend`

### Authentication/Login Issues
If you're prompted for a password:
1. The default credentials are: **admin/admin**
2. Check if `data/config/config.yaml` exists with proper auth settings
3. If not, run `./test-setup.sh` to create the proper config
4. Restart the containers: `docker compose restart`
5. The API key is set to: **bazarr**

If you still have issues:
- Delete the data directory: `rm -rf data/`
- Run the setup script: `./test-setup.sh`
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

# Rebuild from scratch
docker compose up --build
```

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
    ├── data/ → persistent data
    ├── Dockerfile.backend → Python/Alpine backend image
    ├── Dockerfile.frontend → Node.js frontend image (dev-optimized)
    ├── docker-compose.yml → Orchestration config
    ├── test-setup.sh → Setup validation script
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
```

## Next Steps

1. Start developing - all changes are live!
2. Test your modifications at http://localhost:6767 and http://localhost:5173
3. Submit pull requests to the main repository

Happy coding! 🚀
