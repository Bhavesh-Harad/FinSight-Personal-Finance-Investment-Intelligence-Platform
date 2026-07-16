from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Income
from app.incomes.forms import IncomeForm
import datetime

incomes = Blueprint('incomes', __name__)

@incomes.route("/incomes")
@login_required
def list_incomes():
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    today = datetime.date.today()
    if not month: month = today.month
    if not year: year = today.year
    
    all_incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    monthly_incomes = [i for i in all_incomes if i.date.month == month and i.date.year == year]
    
    total = sum(i.amount for i in monthly_incomes)
    
    return render_template('incomes/list.html', title='Incomes', incomes=monthly_incomes, 
                           month=month, year=year, total=total)

@incomes.route("/income/new", methods=['GET', 'POST'])
@login_required
def new_income():
    form = IncomeForm()
    if form.validate_on_submit():
        income = Income(title=form.title.data, amount=form.amount.data, 
                        source=form.source.data, date=form.date.data, 
                        description=form.description.data, user_id=current_user.id)
        db.session.add(income)
        db.session.commit()
        flash('Income has been added successfully!', 'success')
        return redirect(url_for('incomes.list_incomes'))
    elif request.method == 'GET':
        form.date.data = datetime.date.today()
        
    return render_template('incomes/create.html', title='Add Income', form=form)

@incomes.route("/income/<int:income_id>/delete", methods=['POST'])
@login_required
def delete_income(income_id):
    income = Income.query.get_or_404(income_id)
    if income.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('incomes.list_incomes'))
        
    db.session.delete(income)
    db.session.commit()
    flash('Income deleted!', 'info')
    return redirect(url_for('incomes.list_incomes'))
