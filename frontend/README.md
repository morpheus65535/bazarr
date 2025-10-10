# Bazarr Frontend

## Dependencies

- Either [Node.js](https://nodejs.org/) installed manually or using [Node Version Manager](https://github.com/nvm-sh/nvm)
- npm (included in Node.js)
- (Optional) [Docker](https://www.docker.com/) for building and running the frontend using a Docker image

> The recommended Node version to use and maintained is managed on the `.nvmrc` file. You can either install manually
> or use `nvm install` followed by `nvm use`.

## Getting Started

1. Clone or download this repository

   ```
   $ git clone https://github.com/morpheus65535/bazarr.git
   $ cd bazarr/frontend
   ```

2. Install build dependencies in the project directory

   ```
   $ npm install
   ```

3. (Optional) Duplicate `.env.development` file and rename to `.env.development.local`

   ```
   $ cp .env.development .env.development.local
   ```

4. (Optional) Update your backend server's API key in `.env.development.local`

   ```
   # API key of your backend
   VITE_API_KEY="YOUR_SERVER_API_KEY"
   ```

5. (Optional) Change the address of your backend server

   ```
   # Address of your backend
   VITE_PROXY_URL=http://localhost:6767
   ```

6. Run Bazarr backend

   ```
   $ python3 ../bazarr.py
   ```

7. Run the web development tool

   ```
   $ npm start
   ```

## Building with Docker

For Docker-based development, please use the comprehensive development environment provided in the `dev-setup` folder:

```bash
cd ../dev-setup
docker compose up --build
```

This will start both the backend and frontend in separate optimized containers with live reloading enabled.

### Benefits of the dev-setup Docker Environment

- **Full Stack**: Runs both backend and frontend with proper networking
- **Live Reloading**: Changes to your code are immediately reflected
- **Consistency**: Ensures the app runs in the same environment across all systems
- **Isolation**: Avoids dependency conflicts with other projects on your machine
- **Optimized**: Separate containers for backend (Python/Alpine) and frontend (Node.js)

For more details, see the [dev-setup README](../dev-setup/README.md).

3. Open the app in your browser at `http://localhost:5173`.

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.
Open `http://localhost:5173` to view it in the browser.

The page will reload if you make edits.
You will also see any lint errors in the console.

### `npm run build`

Builds the app in production mode and save to the `build` folder.

### `npm run format`

Format code for all files in `frontend` folder

This command will be automatically triggered before any commits to git. Run manually if you modify `.prettierignore` or `.prettierrc`.
