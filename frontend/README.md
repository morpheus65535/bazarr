# Bazarr Frontend

## Dependencies
* [Node.js](https://nodejs.org/)
* npm (included in Node.js)

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
4. Duplicate `.env` file and rename to `.env.local`

   ```
   $ cp .env .env.local
   ```
6. Fill any variable that defined in `.env.local`
7. Run Bazarr backend (Backend must listening on `http://localhost:6767`)

   ```
   $ python3 ../bazarr.py
   ```
9. Run the web client for local development

   ```
   $ npm start
   ```

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.
Open `http://localhost:3000` to view it in the browser.

The page will reload if you make edits.
You will also see any lint errors in the console.

### `npm run build`

Builds the app for production to the `build` folder.

### `npm run lint`

Format code for all files in `frontend` folder

This command will be automatic triggered before any commits to git. Run manually if you modify `.prettierignore` or `.prettierrc`
