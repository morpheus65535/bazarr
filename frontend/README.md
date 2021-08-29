# Bazarr Frontend

## Dependencies

- [Node.js](https://nodejs.org/)
- npm (included in Node.js)

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

3. Duplicate `.env.development` file and rename to `.env.local`

   ```
   $ cp .env .env.local
   ```

4. Update your backend server's API key in `.env.local`

   ```
   # API key of your backend
   REACT_APP_APIKEY="YOUR_SERVER_API_KEY"
   ```

5. Change the address of your backend server (Optional)

   > http://localhost:6767 will be used by default

   ```
   # Address of your backend
   REACT_APP_PROXY_URL=http://localhost:6767
   ```

6. Run Bazarr backend

   ```
   $ python3 ../bazarr.py
   ```

7. Run the web development tool

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

### `npm test`

Run the Unit Test to validate app state.

Please ensure all tests are passed before uploading the code

### `npm run build`

Builds the app for production to the `build` folder.

### `npm run lint`

Format code for all files in `frontend` folder

This command will be automatic triggered before any commits to git. Run manually if you modify `.prettierignore` or `.prettierrc`
