from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from datetime import datetime
from app.models import Goal, Expense, Income
from app.goals.forms import GoalForm, DepositFundsForm, WithdrawFundsForm

goals = Blueprint('goals', __name__)

@goals.route("/goals")
@login_required
def dashboard():
    all_goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.deadline).all()
    
    total_target = sum(g.target_amount for g in all_goals)
    total_saved = sum(g.current_amount for g in all_goals)
    overall_progress = (total_saved / total_target * 100) if total_target > 0 else 0

    return render_template('goals/dashboard.html', title='Financial Goals',
                           goals=all_goals,
                           total_target=total_target,
                           total_saved=total_saved,
                           overall_progress=overall_progress)

@goals.route("/goal/new", methods=['GET', 'POST'])
@login_required
def new_goal():
    form = GoalForm()
    if form.validate_on_submit():
        goal = Goal(name=form.name.data, target_amount=form.target_amount.data,
                    current_amount=0.0, deadline=form.deadline.data,
                    category=form.category.data, user_id=current_user.id)
        db.session.add(goal)
        db.session.commit()
        
        flash('Goal created successfully! You can now deposit funds into it from your savings.', 'success')
            
        return redirect(url_for('goals.dashboard'))
    return render_template('goals/create_edit.html', title='New Goal', form=form, legend='New Goal')

@goals.route("/goal/<int:goal_id>/update", methods=['GET', 'POST'])
@login_required
def update_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.author != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('goals.dashboard'))
    
    form = GoalForm()
    if form.validate_on_submit():
        goal.name = form.name.data
        goal.target_amount = form.target_amount.data
        goal.deadline = form.deadline.data
        goal.category = form.category.data
        db.session.commit()
        
        flash('Goal updated successfully!', 'success')
        return redirect(url_for('goals.dashboard'))
    elif request.method == 'GET':
        form.name.data = goal.name
        form.target_amount.data = goal.target_amount
        form.deadline.data = goal.deadline
        form.category.data = goal.category
    return render_template('goals/create_edit.html', title='Update Goal', form=form, legend='Update Goal')

@goals.route("/goal/<int:goal_id>/delete", methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.author != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('goals.dashboard'))
    db.session.delete(goal)
    db.session.commit()
    flash('Goal deleted successfully!', 'success')
    return redirect(url_for('goals.dashboard'))

@goals.route("/goal/<int:goal_id>/deposit", methods=['GET', 'POST'])
@login_required
def deposit_funds(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.author != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('goals.dashboard'))
    
    form = DepositFundsForm()
    if form.validate_on_submit():
        deposit_amount = form.amount.data
        available_savings = current_user.get_available_savings()
        

        goal.current_amount += deposit_amount
        
        # Log as an expense
        desc = f"Goal Deposit: {goal.name}"
        e = Expense(title=desc, amount=deposit_amount, category="Savings Goal",
                    payment_mode="Bank Transfer", description=desc,
                    date=datetime.utcnow().date(), user_id=current_user.id)
        db.session.add(e)
        
        db.session.commit()
        
        if deposit_amount > available_savings:
            flash(f'Warning: You deposited ₹{deposit_amount:,.2f}, which exceeds your available savings of ₹{available_savings:,.2f}!', 'danger')
        else:
            flash(f'Successfully transferred ₹{deposit_amount:,.2f} from Savings to {goal.name}!', 'success')
        return redirect(url_for('goals.dashboard'))
        
    return render_template('goals/deposit.html', title='Deposit Funds', form=form, goal=goal)

@goals.route("/goal/<int:goal_id>/withdraw", methods=['GET', 'POST'])
@login_required
def withdraw_funds(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.author != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('goals.dashboard'))
    
    form = WithdrawFundsForm()
    if form.validate_on_submit():
        withdraw_amount = form.amount.data
        
        if withdraw_amount > goal.current_amount:
            flash(f'Cannot withdraw more than the current goal amount of ₹{goal.current_amount:,.2f}.', 'danger')
            return redirect(url_for('goals.dashboard'))
            
        goal.current_amount -= withdraw_amount
        
        # Log as an income to return to unallocated pool
        desc = f"Goal Withdrawal: {goal.name}"
        i = Income(title=desc, amount=withdraw_amount, source="Savings Goal",
                   date=datetime.utcnow().date(), user_id=current_user.id)
        db.session.add(i)
        
        db.session.commit()
        
        flash(f'Successfully withdrew ₹{withdraw_amount:,.2f} from {goal.name} back to Savings!', 'success')
        return redirect(url_for('goals.dashboard'))
        
    return render_template('goals/withdraw.html', title='Withdraw Funds', form=form, goal=goal)
