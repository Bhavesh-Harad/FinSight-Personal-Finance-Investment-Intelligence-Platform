from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from app.models import Budget, Expense, Income
from app.budgets.forms import BudgetForm

budgets = Blueprint('budgets', __name__)

@budgets.route("/budgets")
@login_required
def list_budgets():
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    import datetime
    today = datetime.date.today()
    if not month: month = today.month
    if not year: year = today.year
    
    user_budgets = Budget.query.filter_by(user_id=current_user.id, month=month, year=year).all()
    
    # Calculate utilization
    budget_data = []
    budget_categories = [b.category for b in user_budgets if b.category != 'Overall']
    
    for b in user_budgets:
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        monthly_expenses = [e for e in expenses if e.date.month == b.month and e.date.year == b.year and e.category not in ['Savings Goal', 'Investment']]
        
        if b.category == 'Overall':
            spent = sum(e.amount for e in monthly_expenses)
        elif b.category == 'Other':
            spent = sum(e.amount for e in monthly_expenses if e.category == 'Other' or e.category not in budget_categories)
        else:
            spent = sum(e.amount for e in monthly_expenses if e.category == b.category)
        percentage = (spent / b.amount * 100) if b.amount > 0 else 0
        budget_data.append({
            'budget': b,
            'spent': spent,
            'percentage': round(percentage, 1),
            'alert_class': 'bg-danger' if percentage > 80 else ('bg-warning' if percentage > 50 else 'bg-success')
        })
        
    return render_template('budgets/list.html', title='Budgets', budgets=budget_data, month=month, year=year)

@budgets.route("/budget/new", methods=['GET', 'POST'])
@login_required
def new_budget():
    form = BudgetForm()
    if form.validate_on_submit():
        # Get total income for the month
        incomes = Income.query.filter_by(user_id=current_user.id).all()
        monthly_incomes = [i for i in incomes if i.date.month == int(form.month.data) and i.date.year == form.year.data]
        total_income = sum(i.amount for i in monthly_incomes)
        
        # Get existing budgets for the month
        existing_budgets = Budget.query.filter_by(user_id=current_user.id, month=int(form.month.data), year=form.year.data).all()
        current_budget_total = sum(b.amount for b in existing_budgets if b.category != 'Overall')
        
        overall_budget = next((b for b in existing_budgets if b.category == 'Overall'), None)
        
        if form.category.data == 'Overall':
            proposed_overall = form.amount.data
            if proposed_overall > total_income:
                flash(f'Cannot set budget. Your proposed overall budget (₹{proposed_overall}) exceeds your total income (₹{total_income}) for {form.month.data}/{form.year.data}.', 'danger')
                return render_template('budgets/create_edit.html', title='New Budget', form=form, legend='New Budget')
            if proposed_overall < current_budget_total:
                flash(f'Cannot set overall budget to ₹{proposed_overall} because the sum of your individual category budgets (₹{current_budget_total}) exceeds it.', 'danger')
                return render_template('budgets/create_edit.html', title='New Budget', form=form, legend='New Budget')
        else:
            proposed_category_total = current_budget_total + form.amount.data
            if overall_budget:
                if proposed_category_total > overall_budget.amount:
                    flash(f'Cannot set budget. The sum of your category budgets (₹{proposed_category_total}) would exceed your Overall budget (₹{overall_budget.amount}).', 'danger')
                    return render_template('budgets/create_edit.html', title='New Budget', form=form, legend='New Budget')
            else:
                if proposed_category_total > total_income:
                    flash(f'Cannot set budget. Your proposed total budget (₹{proposed_category_total}) exceeds your total income (₹{total_income}) for {form.month.data}/{form.year.data}.', 'danger')
                    return render_template('budgets/create_edit.html', title='New Budget', form=form, legend='New Budget')

        # Check if budget for category already exists for this month/year
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id, 
            category=form.category.data,
            month=int(form.month.data),
            year=form.year.data
        ).first()
        
        if existing_budget:
            flash(f'A budget for {form.category.data} already exists for this month. Please update it instead.', 'warning')
            return redirect(url_for('budgets.list_budgets'))
            
        budget = Budget(category=form.category.data, amount=form.amount.data, 
                        month=int(form.month.data), year=form.year.data, 
                        user_id=current_user.id)
        db.session.add(budget)
        db.session.commit()
        flash('Budget created successfully!', 'success')
        return redirect(url_for('budgets.list_budgets'))
    return render_template('budgets/create_edit.html', title='New Budget', form=form, legend='New Budget')

@budgets.route("/budget/<int:budget_id>/update", methods=['GET', 'POST'])
@login_required
def update_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    if budget.author != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('budgets.list_budgets'))
    
    form = BudgetForm()
    if form.validate_on_submit():
        # Get total income for the month
        incomes = Income.query.filter_by(user_id=current_user.id).all()
        monthly_incomes = [i for i in incomes if i.date.month == int(form.month.data) and i.date.year == form.year.data]
        total_income = sum(i.amount for i in monthly_incomes)
        
        # Get existing budgets for the month
        existing_budgets = Budget.query.filter_by(user_id=current_user.id, month=int(form.month.data), year=form.year.data).all()
        # Sum of other budgets (excluding this one)
        current_budget_total = sum(b.amount for b in existing_budgets if b.id != budget.id and b.category != 'Overall')
        
        overall_budget = next((b for b in existing_budgets if b.id != budget.id and b.category == 'Overall'), None)
        if budget.category == 'Overall' and form.category.data == 'Overall':
            # We are updating the overall budget itself, so it shouldn't be in existing_budgets anymore.
            pass
        elif form.category.data == 'Overall':
            # We are changing a category budget TO an overall budget, handle that logic if overall already exists...
            # The duplicate check later will catch if Overall already exists.
            pass

        if form.category.data == 'Overall':
            proposed_overall = form.amount.data
            if proposed_overall > total_income:
                flash(f'Cannot set budget. Your proposed overall budget (₹{proposed_overall}) exceeds your total income (₹{total_income}) for {form.month.data}/{form.year.data}.', 'danger')
                return render_template('budgets/create_edit.html', title='Update Budget', form=form, legend='Update Budget')
            if proposed_overall < current_budget_total:
                flash(f'Cannot set overall budget to ₹{proposed_overall} because the sum of your individual category budgets (₹{current_budget_total}) exceeds it.', 'danger')
                return render_template('budgets/create_edit.html', title='Update Budget', form=form, legend='Update Budget')
        else:
            proposed_category_total = current_budget_total + form.amount.data
            # If the user is renaming an Overall budget TO a category budget, overall_budget will be None.
            if budget.category == 'Overall' and form.category.data != 'Overall':
                overall_budget = None 
                
            if overall_budget:
                if proposed_category_total > overall_budget.amount:
                    flash(f'Cannot set budget. The sum of your category budgets (₹{proposed_category_total}) would exceed your Overall budget (₹{overall_budget.amount}).', 'danger')
                    return render_template('budgets/create_edit.html', title='Update Budget', form=form, legend='Update Budget')
            else:
                if proposed_category_total > total_income:
                    flash(f'Cannot set budget. Your proposed total budget (₹{proposed_category_total}) exceeds your total income (₹{total_income}) for {form.month.data}/{form.year.data}.', 'danger')
                    return render_template('budgets/create_edit.html', title='Update Budget', form=form, legend='Update Budget')

        # Check for duplicates when changing category/month/year
        duplicate = Budget.query.filter_by(
            user_id=current_user.id, 
            category=form.category.data,
            month=int(form.month.data),
            year=form.year.data
        ).first()
        
        if duplicate and duplicate.id != budget.id:
            flash(f'A budget for {form.category.data} already exists for this month.', 'warning')
            return render_template('budgets/create_edit.html', title='Update Budget', form=form, legend='Update Budget')
            
        budget.category = form.category.data
        budget.amount = form.amount.data
        budget.month = int(form.month.data)
        budget.year = form.year.data
        db.session.commit()
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budgets.list_budgets'))
    elif request.method == 'GET':
        form.category.data = budget.category
        form.amount.data = budget.amount
        form.month.data = budget.month
        form.year.data = budget.year
    return render_template('budgets/create_edit.html', title='Update Budget', form=form, legend='Update Budget')

@budgets.route("/budget/<int:budget_id>/delete", methods=['POST'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    if budget.author != current_user:
        flash('You are not authorized to delete this budget.', 'danger')
        return redirect(url_for('budgets.list_budgets'))
    db.session.delete(budget)
    db.session.commit()
    flash('Your budget has been deleted!', 'success')
    return redirect(url_for('budgets.list_budgets'))
