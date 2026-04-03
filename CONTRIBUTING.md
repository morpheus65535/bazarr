# How to Contribute

## Tools required

- Python 3.8.x to 3.12.x (3.10.x is highly recommended and 3.13 or greater is proscribed).
- Pycharm or Visual Studio code IDE are recommended but if you're happy with VIM, enjoy it!
- Git.
- UI testing must be done using Chrome latest version.

## Development Setup

### Option 1: Full local environment (Docker)

The recommended path for backend or full-stack changes. Runs both the Python backend
and the Vite frontend in Docker containers with live reloading — no local Node.js or
Python required on your host.

See **[dev-setup/README.md](dev-setup/README.md)** for setup instructions.

### Option 2: Local frontend against a running Bazarr instance

Useful when you're making frontend-only changes and already have Bazarr running
elsewhere (a home server, NAS, etc.). Runs the Vite dev server locally and proxies
API calls to your existing instance.

**Prerequisites:** Node.js 20.x

1. Create `frontend/.env.local` (this file is gitignored):

   ```
   VITE_PROXY_URL=http://<your-bazarr-host>:<port>
   VITE_PROXY_SECURE=false
   VITE_ALLOW_WEBSOCKET=true
   VITE_API_KEY=<your API key from Settings > General > Security>
   ```

2. Start the dev server:

   ```bash
   cd frontend
   npm install
   npm start
   ```

   The Vite server opens at `http://localhost:5173` by default. All `/api/*`
   requests are proxied to `VITE_PROXY_URL`.

> **Note:** `VITE_API_KEY` is required. Without it, the frontend attempts to read
> a local `config.yaml` that doesn't exist in a dev checkout and will fail to load.

## Warning

As we're using Git in the development process, you better disable automatic update of Bazarr in UI or you may get your changes overwritten. Alternatively, you can completely disable the update module by running Bazarr with `--no-update` command line argument.

## Branching

### Basic rules

- `master` contains only stable releases (which have been merged to `master`) and is intended for end-users.
- `development` is the target for testing (around 10% of users) and is not intended for end-users looking for stability.
- `feature` is a temporary feature branch based on `development`.

### Conditions

- `master` is not merged back to `development`.
- `development` is not re-based on `master`.
- all `feature` branches are branched from `development` only.
- Bugfixes created specifically for a feature branch are done there (because they are specific, they're not cherry-picked to `development`).
- We will not release a patch (1.0.x) if a newer minor (1.x.0) has already been released. We only go forward.

## Typical contribution workflow

### Community devs

- Fork the repository or pull the latest changes if you already have forked it.
- Checkout `development` branch.
- Make the desired changes.
- Submit a PR to Bazarr `development` branch.
- Once reviewed, your PR will be merged using Squash and Merge with a meaningful commit message matching our standards.

### Official devs team

- All commits must have a meaningful commit message (ex.: Fixed issue with this, Improved process abc, Added input field to UI, etc.).
- Fixes can be made directly to `development` branch but keep in mind that a pre-release with a beta versioning will be created every day a new push is made.
- Features must be developed in dedicated feature branch and merged back to `development` branch using PR.
- Once reviewed, your PR will be merged by morpheus65535 using Squash and Merge with a meaningful message.
