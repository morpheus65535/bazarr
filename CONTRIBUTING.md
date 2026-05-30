# How to Contribute

## Tools required

- Python 3.10.x to 3.13.x (3.13.x is highly recommended). Using any version 3.14 or greater is not allowed as it might break backward compatibility with the libraries we use.
- Pycharm or Visual Studio Code are recommended IDEs but if you're happy with VIM, enjoy it!
- Git.
- UI testing must be done using the latest versions of Chrome and Firefox.

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

As we're using Git in the development process, you should disable automatic updating of Bazarr in the UI General Settings or you will get your changes overwritten. Alternatively, you can completely disable the update module by running Bazarr with `--no-update` command line argument.

## Branching

### Basic rules

- `master` contains only stable releases (which have been merged to `master`) and is intended for end-users.
- `development` is the target used for bleeding-edge feature development, bug fixing and testing (around 10% of users) and is not intended for end-users looking for stability.
- `feature` is a temporary feature branch based on `development`.

### Conditions

- `master` is not merged back to `development`.
- `development` is not re-based on `master`.
- all `feature` branches are branched from `development` only.
- Bugfixes created specifically for a feature branch are done there (and because they are specific to a feature branch, they're not cherry-picked to `development`).
- We will not release a patch for an older major branch (1.0.x) if a newer minor branch (1.x.0) has already been released. We only go forward.

## Typical contribution workflow

### Community developers

- Fork the repository or pull the latest changes if you already have forked it.
- Checkout `development` branch.
- Make the desired changes.
- Submit a PR to Bazarr `development` branch.
- Once reviewed, your PR will be merged using Squash and Merge with a meaningful commit message matching our standards.

### Official development team

- All commits must have a meaningful commit message (ex.: Fixed issue with this, Improved process abc, Added input field to UI, etc.).
- Fixes can be made directly to `development` branch but keep in mind that a pre-release with beta versioning will be created each day a new push is made.
- Features must be developed in a dedicated feature branch and merged back to `development` branch using Pull Requests (PRs).
- Once reviewed, your PR will be merged by morpheus65535 using Squash and Merge with a meaningful message.

# Bazarr Contributor Code of Conduct: Working with AI

We welcome the use of AI tools as productivity enhancers, but development must always be human-led. Whether your Pull Request consists of hand-written code or AI-assisted modifications, all submissions must adhere to the following framework:

---

## Core Expectations

### 1. Own Your Code (Comprehension)

This is our absolute baseline requirement: **never submit code you do not fully understand.** You must be the architect of your changes, using AI strictly as an assistant. 

* You must be able to explain the logic and mechanics of your submission in your own words.
* You must completely understand the underlying purpose (**the "why"**) behind the modification.

### 2. Connect Before You Code (Collaboration)

We operate as a team. To prevent redundant efforts and ensure your approach aligns with the project's roadmap, you must coordinate with us before diving into a new feature.

* **Action Item:** Drop into our Discord server to discuss your ideas and get greenlit before you start working. You can find the Bazarr development community at https://discord.gg/BDCyJPTjx

### 3. Maintain Complete Transparency (Disclosure)

Be entirely upfront about your use of generative tools. If you are directing the AI responsibly and following these principles, explaining your methodology and justifying your design choices to reviewers should be simple and straightforward.

---

## Testing & Quality Standards

Code cannot be evaluated or tested in isolation. Before opening a Pull Request, you are expected to rigorously validate your work against the actual application ecosystem:

```
[Isolated Test] ──> [Live Bazarr Instance + Real Data] ──> [Cross-Platform & Python Version Checks]
```

* **Live Validation:** Run your changes within a live, functioning instance of Bazarr utilizing real-world data.
* **Scope of Impact:** Look beyond the immediate fix. Test adjacent workflows and connected components to ensure no regressions have been introduced.
* **Environment Diversity:** As possible, verify that your code behaves consistently across different operating systems and supported Python versions (which are detailed earlier within this document).