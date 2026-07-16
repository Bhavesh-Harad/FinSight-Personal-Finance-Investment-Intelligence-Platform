from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Budget
from app.expenses.forms import ExpenseForm

expenses = Blueprint('expenses', __name__)

@expenses.route("/expenses")
@login_required
def list_expenses():
    category_filter = request.args.get('category')
    sort_by = request.args.get('sort_by', 'date_desc')
    
    query = Expense.query.filter_by(user_id=current_user.id)
    
    if category_filter:
        query = query.filter_by(category=category_filter)
        
    if sort_by == 'date_asc':
        query = query.order_by(Expense.date.asc())
    elif sort_by == 'amount_desc':
        query = query.order_by(Expense.amount.desc())
    elif sort_by == 'amount_asc':
        query = query.order_by(Expense.amount.asc())
    else:
        query = query.order_by(Expense.date.desc())
        
    all_expenses = query.all()
    
    return render_template('expenses/list.html', title='Expenses', expenses=all_expenses)

@expenses.route("/expense/new", methods=['GET', 'POST'])
@login_required
def new_expense():
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
            flash('Your expense has been added!', 'success')
            
        db.session.commit()
        return redirect(url_for('expenses.list_expenses'))
    return render_template('expenses/create_edit.html', title='New Expense', form=form, legend='New Expense')

@expenses.route("/expense/<int:expense_id>/update", methods=['GET', 'POST'])
@login_required
def update_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.author != current_user:
        flash('You are not authorized to edit this expense.', 'danger')
        return redirect(url_for('expenses.list_expenses'))
    form = ExpenseForm()
    if form.validate_on_submit():
        expense.title = form.title.data
        expense.amount = form.amount.data
        expense.category = form.category.data
        expense.payment_mode = form.payment_mode.data
        expense.date = form.date.data
        expense.description = form.description.data
        db.session.commit()
        flash('Your expense has been updated!', 'success')
        return redirect(url_for('expenses.list_expenses'))
    elif request.method == 'GET':
        form.title.data = expense.title
        form.amount.data = expense.amount
        form.category.data = expense.category
        form.payment_mode.data = expense.payment_mode
        form.date.data = expense.date
        form.description.data = expense.description
    return render_template('expenses/create_edit.html', title='Update Expense', form=form, legend='Update Expense')

@expenses.route("/expense/<int:expense_id>/delete", methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.author != current_user:
        flash('You are not authorized to delete this expense.', 'danger')
        return redirect(url_for('expenses.list_expenses'))
    db.session.delete(expense)
    db.session.commit()
    flash('Your expense has been deleted!', 'success')
    return redirect(url_for('expenses.list_expenses'))
