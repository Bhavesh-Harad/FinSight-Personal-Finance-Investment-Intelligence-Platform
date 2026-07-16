from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from app.models import Investment, Expense
from app.investments.forms import InvestmentForm
import yfinance as yf



investments = Blueprint('investments', __name__)

@investments.route("/investments")
@login_required
def dashboard():
    all_investments = Investment.query.filter_by(user_id=current_user.id).order_by(Investment.purchase_date.desc()).all()

    total_invested = sum(i.total_invested() for i in all_investments)
    current_value = sum(i.current_value() for i in all_investments)
    total_return = current_value - total_invested
    percentage_return = (total_return / total_invested * 100) if total_invested > 0 else 0
    
    # Calculate most recent update time
    latest_update = None
    for i in all_investments:
        if i.last_updated:
            if not latest_update or i.last_updated > latest_update:
                latest_update = i.last_updated
    
    
    # Asset Allocation
    allocation = {}
    for i in all_investments:
        allocation[i.asset_class] = allocation.get(i.asset_class, 0) + i.current_value()
        
    pie_labels = list(allocation.keys())
    pie_data = list(allocation.values())

    return render_template('investments/dashboard.html', title='Investment Portfolio',
                           investments=all_investments,
                           total_invested=total_invested,
                           current_value=current_value,
                           total_return=total_return,
                           percentage_return=percentage_return,
                           pie_labels=pie_labels, pie_data=pie_data,
                           latest_update=latest_update)

@investments.route("/investment/new", methods=['GET', 'POST'])
@login_required
def new_investment():
    form = InvestmentForm()
    if form.validate_on_submit():
        total_cost = form.purchase_price.data * form.quantity.data
        available_savings = current_user.get_available_savings()
        
        current_price = form.current_price.data
        last_updated = None
        if not current_price and form.symbol.data:
            try:
                ticker = yf.Ticker(form.symbol.data.strip().upper())
                last_price = ticker.fast_info['lastPrice']
                if last_price and last_price > 0:
                    current_price = float(last_price)
                    from datetime import datetime
                    last_updated = datetime.utcnow()
            except Exception:
                pass
        
        if not current_price:
            current_price = form.purchase_price.data
        
        inv = Investment(name=form.name.data, symbol=form.symbol.data,
                         asset_class=form.asset_class.data, purchase_date=form.purchase_date.data,
                         purchase_price=form.purchase_price.data, quantity=form.quantity.data,
                         current_price=current_price, last_updated=last_updated, user_id=current_user.id)
        db.session.add(inv)
        
        # Log as an expense
        desc = f"Investment: {inv.name} ({inv.quantity} shares)"
        e = Expense(title=desc, amount=total_cost, category="Investment", 
                    payment_mode="Bank Transfer", description=desc,
                    date=inv.purchase_date, user_id=current_user.id)
        db.session.add(e)
        
        db.session.commit()
        
        if total_cost > available_savings:
            flash(f'Warning: This investment of ${total_cost:,.2f} exceeds your available savings of ${available_savings:,.2f}!', 'danger')
        else:
            flash('Investment added successfully!', 'success')
            
        return redirect(url_for('investments.dashboard'))
    return render_template('investments/create_edit.html', title='New Investment', form=form, legend='New Investment')

@investments.route("/investment/<int:inv_id>/update", methods=['GET', 'POST'])
@login_required
def update_investment(inv_id):
    inv = Investment.query.get_or_404(inv_id)
    if inv.author != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('investments.dashboard'))
    
    form = InvestmentForm()
    if form.validate_on_submit():
        old_cost = inv.total_invested()
        new_cost = form.purchase_price.data * form.quantity.data
        cost_difference = new_cost - old_cost
        available_savings = current_user.get_available_savings()
        
        current_price = form.current_price.data
        last_updated = None
        if not current_price and form.symbol.data:
            try:
                ticker = yf.Ticker(form.symbol.data.strip().upper())
                last_price = ticker.fast_info['lastPrice']
                if last_price and last_price > 0:
                    current_price = float(last_price)
                    from datetime import datetime
                    last_updated = datetime.utcnow()
            except Exception:
                pass
        
        if not current_price:
            current_price = form.purchase_price.data

        inv.name = form.name.data
        inv.symbol = form.symbol.data
        inv.asset_class = form.asset_class.data
        inv.purchase_date = form.purchase_date.data
        inv.purchase_price = form.purchase_price.data
        inv.quantity = form.quantity.data
        inv.current_price = current_price
        if last_updated:
            inv.last_updated = last_updated
        
        # Log the difference as an expense (or refund if negative)
        if cost_difference > 0:
            desc = f"Investment Update: Added capital to {inv.name}"
            e = Expense(title=desc, amount=cost_difference, category="Investment", 
                        payment_mode="Bank Transfer", description=desc,
                        date=inv.purchase_date, user_id=current_user.id)
            db.session.add(e)
        
        db.session.commit()
        
        if cost_difference > available_savings:
            flash(f'Warning: This update requires ${cost_difference:,.2f} of new capital, which exceeds your available savings of ${available_savings:,.2f}!', 'danger')
        else:
            flash('Investment updated successfully!', 'success')
        return redirect(url_for('investments.dashboard'))
    elif request.method == 'GET':
        form.name.data = inv.name
        form.symbol.data = inv.symbol
        form.asset_class.data = inv.asset_class
        form.purchase_date.data = inv.purchase_date
        form.purchase_price.data = inv.purchase_price
        form.quantity.data = inv.quantity
        form.current_price.data = inv.current_price
    return render_template('investments/create_edit.html', title='Update Investment', form=form, legend='Update Investment')

@investments.route("/investment/<int:inv_id>/delete", methods=['POST'])
@login_required
def delete_investment(inv_id):
    inv = Investment.query.get_or_404(inv_id)
    if inv.author != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('investments.dashboard'))
    db.session.delete(inv)
    db.session.commit()
    flash('Investment deleted successfully!', 'success')
    return redirect(url_for('investments.dashboard'))

@investments.route("/api/price/<symbol>")
@login_required
def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol.strip().upper())
        last_price = ticker.fast_info['lastPrice']
        if last_price and last_price > 0:
            return {'price': float(last_price)}
    except Exception:
        pass
    return {'price': None}, 404
