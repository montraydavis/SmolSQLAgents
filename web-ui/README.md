# Flask + React Application

This is a simple full-stack application with a Python Flask backend and React frontend.

## Project Structure

```
web-ui/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── venv/              # Python virtual environment
└── frontend/
    ├── src/
    │   ├── App.js         # React component that fetches from API
    │   └── ...
    └── package.json       # Node.js dependencies
```

## Setup Instructions

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Activate the virtual environment (if using Windows):
   ```bash
   venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the Flask server:
   ```bash
   python app.py
   ```

   The backend will be running at `http://127.0.0.1:5000`

### 2. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm start
   ```

   The frontend will be running at `http://localhost:3000`

## How It Works

- The Flask backend provides an API endpoint at `/api/message` that returns a JSON response
- The React frontend fetches this message when the component mounts and displays it
- CORS is enabled on the backend to allow cross-origin requests from the frontend

## API Endpoints

- `GET /api/message` - Returns a simple greeting message

## Technologies Used

- **Backend**: Python, Flask, Flask-CORS
- **Frontend**: React, JavaScript, HTML, CSS 