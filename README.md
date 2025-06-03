# Live Account Tracker

## Overview
This project is a live tracker for Account Executives (AEs) to visualize their progress toward monthly revenue goals. It fetches revenue data from Mother Duck, updates automatically every 2 hours, and displays both individual and team progress in a modern web dashboard.

## Features
- Automated data sync from Mother Duck (every 2 hours)
- FastAPI backend serving revenue data and last updated timestamp
- React frontend with:
  - Individual AE progress bars and charts
  - Editable monthly goals
  - Team goal and progress bar
  - "Last Updated" timestamp

## Setup

### 1. Clone the repository
```sh
git clone https://github.com/ajmares/Live-Account-Tracker.git
cd Live-Account-Tracker
```

### 2. Python Backend
- Install dependencies:
  ```sh
  pip3 install -r requirements.txt
  ```
- Set your Mother Duck API token as an environment variable:
  ```sh
  export MOTHERDUCK_TOKEN=your_token_here
  ```
- Run the backend:
  ```sh
  uvicorn main:app --reload --port 8000
  ```

### 3. Data Fetch Script
- Run manually or let the cron job update every 2 hours:
  ```sh
  python3 fetch_revenue_data.py
  ```

### 4. React Frontend
- Go to the frontend directory and install dependencies:
  ```sh
  cd frontend
  npm install
  npm start
  ```
- Open [http://localhost:3000](http://localhost:3000) in your browser.

## Automation
- The data fetch script is scheduled via `cron` to run every 2 hours and keep the dashboard up to date.

## Customization
- Edit goals directly in the UI for each AE and see team progress update live.

## License
MIT 