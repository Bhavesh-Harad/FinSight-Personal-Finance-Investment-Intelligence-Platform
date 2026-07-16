# FinSight

FinSight is a full-stack personal financial management platform built with Python (Flask) and Bootstrap 5.

## Features (Milestone 1)
- User Authentication (Registration, Login, Profile) with secure passwords
- Expense tracking and categorization
- Budget creation and utilization monitoring
- Dashboard with dynamic charts (Chart.js) and progress bars
- Beautiful, responsive UI with Bootstrap 5 and custom CSS

## Setup Instructions

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd FinSight
   ```

2. **Create a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```
   *Note: The database (`finsight.db`) will be automatically created on the first run.*

5. **Access the application**:
   Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Tech Stack
- **Backend:** Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt, Flask-WTF
- **Database:** SQLite
- **Frontend:** Jinja2 Templates, Bootstrap 5, Chart.js, FontAwesome
