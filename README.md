# FinSight

## What is FinSight?
FinSight is a personal finance and investment intelligence platform designed to help users take control of their money. It provides a centralized, easy-to-use dashboard to monitor incomes, track daily expenses, manage budgets, keep an eye on investment portfolios, and track progress toward long-term financial goals.

## Features Implemented
- **User Authentication:** Secure registration and login system with encrypted passwords and profile management.
- **Financial Dashboard:** A visual overview of your financial health, displaying total savings, spending habits, and dynamic charts.
- **Income & Expense Tracking:** Log and categorize your daily expenses and income sources with dates and payment modes.
- **Budget Monitoring:** Set up monthly or yearly budgets for specific categories and track how much you have utilized.
- **Investment Portfolio:** Track various assets (stocks, mutual funds, real estate). It automatically calculates your absolute returns and percentage returns based on your purchase and current prices.
- **Financial Goals:** Define short-term and long-term goals (e.g., "Emergency Fund" or "New Car"), and the app calculates your progress, remaining time, and required monthly savings.

## Tech Stack Used
- **Backend:** Python, Flask (Web Framework)
- **Database:** SQLite (managed via Flask-SQLAlchemy)
- **Security:** Flask-Bcrypt (Password Hashing), Flask-Login (User Sessions)
- **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 (HTML Templating)
- **Data Visualization:** Chart.js

---

## How to Run the Code from Scratch

Follow these steps to set up and run FinSight on your own computer:

### 1. Clone the Repository
Download the code to your local machine:
```bash
git clone https://github.com/Bhavesh-Harad/FinSight-Personal-Finance-Investment-Intelligence-Platform.git
cd FinSight-Personal-Finance-Investment-Intelligence-Platform
```

### 2. Set Up a Virtual Environment
A virtual environment ensures the project dependencies don't interfere with your system's Python installation.
```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
Install all the required Python libraries using `pip`:
```bash
pip install -r requirements.txt
```

### 4. Recreate the Hidden Configuration Files
For security reasons, some files (like passwords and databases) are ignored by Git (using the `.gitignore` file) and are not uploaded to GitHub. **You must recreate them to run the app:**

**A. The Environment File (`.env`)**
Create a new file named `.env` in the main project folder. Open it in a text editor and add a secret key for Flask security:
```env
SECRET_KEY=your_secure_random_secret_key_here
```

**B. The Database File (`instance/finsight.db`)**
You do *not* need to create the database file manually. When you run the application for the very first time, the code will automatically create the `instance` folder and generate the `finsight.db` database for you!

### 5. Run the Application
Once everything is set up, start the server:
```bash
python run.py
```

### 6. View the App
Open your web browser and go to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

You can now register a new account and explore FinSight!
