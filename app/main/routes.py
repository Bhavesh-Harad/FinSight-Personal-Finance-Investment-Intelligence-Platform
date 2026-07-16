from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Budget, User, Income, Investment, Goal
from app.auth.routes import admin_required
from app.expenses.forms import ExpenseForm
from app.health import calculate_health_score
from datetime import datetime, timedelta
import calendar

main = Blueprint('main', __name__)

@main.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    total_users = len(users)
    admins = sum(1 for u in users if u.role == 'Admin')
    regular_users = total_users - admins
    
    return render_template('dashboard/admin.html', title='User Management',
                           users=users, total_users=total_users, 
                           admins=admins, regular_users=regular_users)

@main.route("/admin/user/<int:user_id>/delete", methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('main.admin_dashboard'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.email} has been deleted.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main.route("/", methods=['GET', 'POST'])
@main.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(title=form.title.data, amount=form.amount.data, 
                          category=form.category.data, payment_mode=form.payment_mode.data,
                          date=form.date.data, description=form.description.data, 
                          user_id=current_user.id)
        db.session.add(expense)
        
        # Check if expense exceeds budget
        monthly_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            db.extract('month', Expense.date) == form.date.data.month,
            db.extract('year', Expense.date) == form.date.data.year
        ).all()
        
        category_budget = Budget.query.filter_by(
            user_id=current_user.id, 
            category=form.category.data, 
            month=form.date.data.month, 
            year=form.date.data.year
        ).first()
        
        overall_budget = Budget.query.filter_by(
            user_id=current_user.id, 
            category='Overall', 
            month=form.date.data.month, 
            year=form.date.data.year
        ).first()

        other_budget = Budget.query.filter_by(
            user_id=current_user.id, 
            category='Other', 
            month=form.date.data.month, 
            year=form.date.data.year
        ).first()
        
        all_month_budgets = Budget.query.filter_by(
            user_id=current_user.id, 
            month=form.date.data.month, 
            year=form.date.data.year
        ).all()
        budget_categories = [b.category for b in all_month_budgets if b.category != 'Overall']
        
        exceeded = False
        
        if category_budget:
            category_spent = sum(e.amount for e in monthly_expenses if e.category == form.category.data) + form.amount.data
            if category_spent > category_budget.amount:
                flash(f'Warning: This expense exceeds your {form.category.data} budget limit!', 'warning')
                exceeded = True
        elif other_budget:
            # If no specific category budget, it falls under 'Other'
            other_spent = sum(e.amount for e in monthly_expenses if e.category == 'Other' or e.category not in budget_categories) + form.amount.data
            if other_spent > other_budget.amount:
                flash(f'Warning: This expense exceeds your Other budget limit!', 'warning')
                exceeded = True
                
        total_spent = sum(e.amount for e in monthly_expenses) + form.amount.data
        if overall_budget and total_spent > overall_budget.amount:
            flash(f'Warning: This expense exceeds your Overall budget limit!', 'warning')
            exceeded = True
            
        if not exceeded:
            flash('Expense added from dashboard!', 'success')
            
        db.session.commit()
        return redirect(url_for('main.dashboard'))

    # Gather data for summary cards
    today = datetime.today()
    current_month = today.month
    current_year = today.year
    
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    
    # Calculate total expenses this month
    monthly_expenses = [e for e in expenses if e.date.month == current_month and e.date.year == current_year]
    total_spent_this_month = sum(e.amount for e in monthly_expenses)
    
    # Calculate budgets this month
    budgets = Budget.query.filter_by(user_id=current_user.id, month=current_month, year=current_year).all()
    overall_budget = next((b for b in budgets if b.category == 'Overall'), None)
    if overall_budget:
        total_budget_this_month = overall_budget.amount
    else:
        total_budget_this_month = sum(b.amount for b in budgets)
    
    # Calculate incomes this month
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    monthly_incomes = [i for i in incomes if i.date.month == current_month and i.date.year == current_year]
    total_income_this_month = sum(i.amount for i in monthly_incomes)
    
    # Budgets with utilization
    budget_progress = []
    budget_categories = [b.category for b in budgets if b.category != 'Overall']
    
    for b in budgets:
        if b.category == 'Overall':
            spent = sum(e.amount for e in monthly_expenses)
        elif b.category == 'Other':
            # Count 'Other' expenses + any expense whose category has no specific budget
            spent = sum(e.amount for e in monthly_expenses if e.category == 'Other' or e.category not in budget_categories)
        else:
            spent = sum(e.amount for e in monthly_expenses if e.category == b.category)
            
        percentage = (spent / b.amount * 100) if b.amount > 0 else 0
        budget_progress.append({
            'category': b.category,
            'amount': b.amount,
            'spent': spent,
            'percentage': round(percentage, 1),
            'alert_class': 'bg-danger' if percentage > 80 else ('bg-warning' if percentage > 50 else 'bg-success')
        })

    # Prepare data for pie chart (Category Breakdown for this month)
    categories = {}
    payment_modes = {}
    for e in monthly_expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount
        payment_modes[e.payment_mode] = payment_modes.get(e.payment_mode, 0) + e.amount
    
    pie_labels = list(categories.keys())
    pie_data = list(categories.values())
    
    pm_pie_labels = list(payment_modes.keys())
    pm_pie_data = list(payment_modes.values())

    # Prepare data for bar chart (Last 6 months spending)
    bar_labels = []
    bar_data = []
    for i in range(5, -1, -1):
        m = (today.replace(day=1) - timedelta(days=28*i)).month
        y = (today.replace(day=1) - timedelta(days=28*i)).year
        # Correctly get month name
        import calendar
        month_name = calendar.month_abbr[m]
        bar_labels.append(f"{month_name} {y}")
        
        m_expenses = Expense.query.filter_by(user_id=current_user.id).all()
        m_total = sum(e.amount for e in m_expenses if e.date.month == m and e.date.year == y)
        bar_data.append(m_total)
    
    recent_transactions = expenses[:5]

    planned_savings = total_income_this_month - total_budget_this_month
    actual_savings = total_income_this_month - total_spent_this_month
    
    health_data = calculate_health_score(current_user)

    return render_template('dashboard/index.html', title='Dashboard', 
                           form=form,
                           total_spent=total_spent_this_month, 
                           total_budget=total_budget_this_month,
                           total_income=total_income_this_month,
                           planned_savings=planned_savings,
                           actual_savings=actual_savings,
                           budget_progress=budget_progress,
                           pie_labels=pie_labels, pie_data=pie_data,
                           pm_pie_labels=pm_pie_labels, pm_pie_data=pm_pie_data,
                           bar_labels=bar_labels, bar_data=bar_data,
                           recent_transactions=recent_transactions,
                           health_data=health_data)

@main.route("/savings")
@login_required
def savings():
    from app.models import Income, Budget
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    incomes = Income.query.filter_by(user_id=current_user.id).all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    
    total_lifetime_income = sum(i.amount for i in incomes)
    total_lifetime_expense = sum(e.amount for e in expenses)
    total_accumulated_savings = total_lifetime_income - total_lifetime_expense
    
    total_invested = sum(inv.total_invested() for inv in current_user.investments)
    total_goals = sum(g.current_amount for g in current_user.goals)
    available_savings = current_user.get_available_savings()
    
    # Calculate month-wise data
    months_data = {}
    
    # Process incomes
    for i in incomes:
        key = f"{i.date.year}-{i.date.month:02d}"
        if key not in months_data:
            months_data[key] = {'income': 0, 'expense': 0, 'budget': 0, 'date_obj': i.date.replace(day=1)}
        months_data[key]['income'] += i.amount
        
    # Process expenses
    for e in expenses:
        key = f"{e.date.year}-{e.date.month:02d}"
        if key not in months_data:
            months_data[key] = {'income': 0, 'expense': 0, 'budget': 0, 'date_obj': e.date.replace(day=1)}
        months_data[key]['expense'] += e.amount
        
    # Process budgets
    for b in budgets:
        key = f"{b.year}-{b.month:02d}"
        if key not in months_data:
            months_data[key] = {'income': 0, 'expense': 0, 'budget': 0, 'date_obj': datetime(b.year, b.month, 1)}
        
        # If there's an Overall budget for this month, use it.
        # Otherwise, sum the categories.
        # It's easier to compute it separately per month:
    
    # Re-evaluate budgets per month to handle 'Overall' correctly
    for key, data in months_data.items():
        year, month = map(int, key.split('-'))
        month_budgets = [b for b in budgets if b.year == year and b.month == month]
        overall_b = next((b for b in month_budgets if b.category == 'Overall'), None)
        if overall_b:
            data['budget'] = overall_b.amount
        else:
            data['budget'] = sum(b.amount for b in month_budgets)
            
        data['planned_savings'] = data['income'] - data['budget']
        data['actual_savings'] = data['income'] - data['expense']
        
    # Sort months descending
    sorted_months = sorted(months_data.values(), key=lambda x: x['date_obj'], reverse=True)
    
    # Chart data (last 12 months, sorted chronologically for chart)
    chart_months = sorted_months[:12]
    chart_months.reverse()
    
    bar_labels = [m['date_obj'].strftime('%b %Y') for m in chart_months]
    bar_data_planned = [m['planned_savings'] for m in chart_months]
    bar_data_actual = [m['actual_savings'] for m in chart_months]

    return render_template('dashboard/savings.html', title='Savings Dashboard',
                           total_accumulated=total_accumulated_savings,
                           total_invested=total_invested,
                           total_goals=total_goals,
                           available_savings=available_savings,
                           months_data=sorted_months,
                           bar_labels=bar_labels,
                           bar_data_planned=bar_data_planned,
                           bar_data_actual=bar_data_actual)
