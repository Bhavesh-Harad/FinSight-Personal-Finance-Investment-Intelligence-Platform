# FinSight: Personal Finance & Investment Intelligence Platform

FinSight is a comprehensive, full-stack personal financial management and investment tracking platform built with Python (Flask) and Bootstrap 5. It empowers users to take control of their finances by tracking expenses, managing incomes, monitoring investments, setting budgets, and achieving financial goals.

## 🌟 Key Features

### 1. User Authentication & Profile Management
- Secure user registration and login (password hashing via Flask-Bcrypt).
- User profile management with roles and verification flags.
- Built-in support for Google OAuth (extendable).

### 2. Comprehensive Dashboard
- Centralized dashboard displaying total available savings.
- Dynamic charts (via Chart.js) for visual breakdown of finances.
- Quick summary of your current financial health.

### 3. Expense & Income Tracking
- **Expenses**: Log title, amount, category, payment mode (Cash, Card, etc.), and date.
- **Incomes**: Track various income sources, amounts, and dates.
- Easily review transaction histories and categorize spending.

### 4. Budget Monitoring
- Create monthly/yearly budgets per category.
- Monitor your budget utilization against your actual logged expenses.

### 5. Investment Portfolio Management
- Track stocks, ETFs, mutual funds, real estate, crypto, and more.
- Log purchase price, quantity, and current price.
- Automatic calculations for **Absolute Returns**, **Percentage Returns**, Total Invested value, and Current value.

### 6. Financial Goal Tracking
- Create Short-term and Long-term financial goals (e.g., "Buy a house", "Emergency Fund").
- Track target amount, current saved amount, and deadlines.
- Automatically calculates progress percentages, remaining amounts, time left, and required monthly savings to hit the goal on time.

---

## 🛠 Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt, Flask-WTF
- **Database:** SQLite (Default for development)
- **Frontend:** HTML5/CSS3, Jinja2 Templates, Bootstrap 5, Chart.js, FontAwesome

---

## 🚀 How to Run Locally on Your Device

Follow these steps to set up and run FinSight on your own computer.

### Prerequisites
- Install **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- Install **Git**: [Download Git](https://git-scm.com/downloads)

### 1. Clone the Repository
Open your terminal (or Command Prompt / PowerShell) and clone the project:
```bash
git clone https://github.com/Bhavesh-Harad/FinSight-Personal-Finance-Investment-Intelligence-Platform.git
cd FinSight-Personal-Finance-Investment-Intelligence-Platform
```
*(If you already have the code locally, just navigate to the project directory via terminal: `cd path/to/FinSight`)*

### 2. Set Up a Virtual Environment (Recommended)
A virtual environment keeps the project's dependencies isolated from your system.
```bash
python -m venv venv
```

**Activate the virtual environment:**
- **On Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **On macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
Install all the required Python packages listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables (Optional but recommended)
Create a `.env` file in the root directory and add a secret key for Flask security:
```env
SECRET_KEY=your_very_secret_key_here
```

### 5. Run the Application
Start the Flask development server.
```bash
python run.py
```
*(Note: The SQLite database `finsight.db` will be automatically generated inside the `instance/` folder the first time you run the app).*

### 6. Access the App
Open your favorite web browser and go to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

You can now register a new account and start tracking your finances!
