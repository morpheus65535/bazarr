# Bazarr Frontend

## How to Run

1. Duplicate `.env` file and rename to `.env.local`
2. Fill any variable that defined in `.env.local`
3. Run Bazarr backend (Backend must listening on `http://localhost:6767`)
4. Start frontend by running `npm start`

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

This command will automatic trigger when you commit codes to git. Run manually if you modify `.prettierignore` or `.prettierrc`
