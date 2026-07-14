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
* **Celery & Celery Beat**: Asynchronous task queue and periodic job scheduler using Redis as the message broker.

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

### 4. Asynchronous & Scheduled Tasks (Celery & Redis Worker Architecture)
This project uses **Celery** for asynchronous task execution (such as CSV exports) and **Celery Beat** for scheduling periodic tasks:

* **Asynchronous Jobs (CSV Export)**: When a trekker requests a CSV export of their booking history, a background job is queued in Celery. The Flask application immediately returns a `task_id` for frontend polling, and the Celery worker compiles the CSV and emails it to the user.
* **Scheduled Reminders**: Bounded to Celery Beat, a daily reminder task checks for bookings starting in 1, 2, or 3 days and sends alert notifications and HTML emails to the trekkers (configured to run daily at 8:00 AM).
* **Monthly Activity Reports**: Bounded to Celery Beat, a report compiling task summarizes platform activity for the past month and emails it to the administrator (configured to run on the 1st of every month at 6:00 AM).

**Running the Background Workers:**
To start the asynchronous tasks and scheduler, run the following commands (with active virtual environment) in the `backend/` directory:

1. **Start the Redis Server**:
   Ensure Redis is running on `127.0.0.1:6379`.
   ```bash
   redis-server
   ```

2. **Start the Celery Worker Process**:
   ```bash
   celery -A celery_app.celery_instance worker --loglevel=info
   ```

3. **Start the Celery Beat Scheduler**:
   ```bash
   celery -A celery_app.celery_instance beat --loglevel=info
   ```

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
