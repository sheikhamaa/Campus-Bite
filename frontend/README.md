# CampusBite Frontend

This is the React frontend for the CampusBite food-ordering platform.

## Tech stack

- React
- Vite
- React Router
- Axios

## Local development

1. Install dependencies:
   npm install
2. Start the app:
   npm run dev
3. Open the browser to the local Vite address (usually http://localhost:5173)

## Production build

npm run build

## Backend API

The frontend expects the API server to be running at:

- http://localhost:8000

If needed, set a custom API URL before running the app:

VITE_API_URL=http://localhost:8000 npm run dev

## Roles included

- Customer
- Owner
- Delivery partner

This frontend supports login, registration, customer ordering, owner restaurant management, and delivery tracking flows.
