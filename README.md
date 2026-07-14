# Trekking Management Platform (TMA)

This is a comprehensive Trekking Management Platform designed for managing treks, bookings, user roles, notifications, and analytics. It supports three distinct user roles: **Admin**, **Staff**, and **Trekker (User)**.

---

## Tech Stack

### Backend
* **Python / Flask (3.1.3)**: RESTful API Development.
* **SQLAlchemy & Flask-SQLAlchemy (3.1.1)**: ORM for Database Management.
* **SQLite**: Lightweight Relational Database.
* **Flask-JWT-Extended (4.7.4)**: Token-based Secure Authentication.
* **Flask-Caching (2.4.0)**: Redis-backed endpoint caching with automatic fallback.
* **Flask-Mail (0.10.0)**: SMTP Email integration for reminders and monthly reports.
* **In-process Threads**: Custom thread-safe task queue and scheduler (no separate Celery daemon needed).

### Frontend
* **Vue 2 (2.7.16)**: Reactive User Interface.
* **Vue Router (3.6.5)**: Single Page Application (SPA) Routing.
* **Axios (1.18.1)**: HTTP client for API communication.
* **Bootstrap (5.3.8)**: Modern, responsive styling.
* **Chart.js (4.4.3)**: Visual analytics on the Admin and Staff dashboards.
* **Vite (5.2.0)**: Lightning-fast build tool and dev server.

---

## How to Start the Project

### 1. Prerequisites
Ensure you have the following installed:
* **Python** (version 3.10 or above)
* **Node.js** (version 18 or above)
* **Redis** (Optional: used for caching. If not running, the application gracefully falls back to `SimpleCache` in memory).

---

### 2. Backend Setup
1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Set up a Virtual Environment**:
   If a virtual environment is not already created, create it:
   ```bash
   python3 -m venv .venv
   ```
   Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
   *(On Windows use: `.venv\Scripts\activate`)*

3. **Install Dependencies**:
   Navigate back to the project root or install from the backend directory:
   ```bash
   pip install -r ../requirements.txt
   ```

4. **Start the Flask Server**:
   ```bash
   python app.py
   ```
   * The server runs on `http://127.0.0.1:5000`.
   * On startup, the database `trekking.db` is initialized automatically, and a default Admin account is created programmatically.
   * Background threads for periodic reminders (daily at 8 AM) and monthly reports (1st of month at 6 AM) are automatically spawned.

---

### 3. Frontend Setup
1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Start the Development Server**:
   ```bash
   npm run dev
   ```
   * The Vite development server starts on `http://localhost:5173`.
   * Requests to `/api/*` are automatically proxied to the backend at `http://localhost:5000`.

---

### 4. Asynchronous & Scheduled Tasks (Worker Architecture)
Although `celery` is listed in `requirements.txt` for compatibility, this project is architected to run asynchronous tasks and periodic schedules **in-process** using Python daemon threads. This eliminates the need for managing a separate Celery worker process or Celery Beat scheduler:

* **Background Worker Thread**: When `app.py` runs, it calls `init_scheduler(app)`. This spawns a background thread that monitors a thread-safe task queue (`queue.Queue`). When a trekker requests a CSV export of their bookings, the task is pushed onto this queue, and the background thread executes the export in the background.
* **Background Scheduler Thread**: A separate background thread checks the system time every 60 seconds. It automatically runs the scheduled daily email reminders (at 8:00 AM) and monthly activity reports (on the 1st of the month at 6:00 AM) without requiring a separate scheduler process.

**Running the tasks**:
Simply starting the Flask application (`python app.py`) automatically starts the scheduler and worker threads. No separate commands (like `celery -A app.celery worker` or `celery -A app.celery beat`) are required.

---

## Default User Accounts

* **Admin Credentials**:
  * **Username**: `admin`
  * **Password**: `Admin@123`
  * **Email**: `admin@gmail.com`

* **Staff Credentials**:
  Can be created through the Admin Panel (`/admin/staff`).

* **Trekker Credentials**:
  Can register directly using the **Sign Up** option on the frontend login page.
