from datetime import datetime

def calculate_health_score(user):
    """
    Calculates a 100-point Financial Health Score based on 4 pillars.
    """
    score = 0
    breakdown = {
        'emergency_fund': {'score': 0, 'max': 30, 'message': 'Insufficient data'},
        'savings_rate': {'score': 0, 'max': 30, 'message': 'Insufficient data'},
        'budget_adherence': {'score': 0, 'max': 20, 'message': 'Insufficient data'},
        'investment_focus': {'score': 0, 'max': 20, 'message': 'Insufficient data'}
    }

    # Lifetime Totals
    total_income = sum(i.amount for i in user.incomes)
    # Note: user.expenses now includes Investment purchases and Goal deposits
    total_expenses = sum(e.amount for e in user.expenses)
    
    # 1. Emergency Fund Strength (30 pts)
    # Logic: Available Savings / Lifetime Average Monthly Expense (excluding investments/goals)
    pure_expenses = sum(e.amount for e in user.expenses if e.category not in ['Investment', 'Savings Goal'])
    
    if pure_expenses > 0 and len(user.expenses) > 0:
        earliest_date = min(e.date for e in user.expenses)
        months_active = max(1, (datetime.utcnow().date() - earliest_date).days / 30.0)
        avg_monthly_pure_expense = pure_expenses / months_active
        
        available_savings = user.get_available_savings()
        months_covered = available_savings / avg_monthly_pure_expense if avg_monthly_pure_expense > 0 else 99
        
        if months_covered >= 6:
            breakdown['emergency_fund']['score'] = 30
            breakdown['emergency_fund']['message'] = f"{months_covered:.1f} months covered. Excellent!"
        elif months_covered >= 3:
            breakdown['emergency_fund']['score'] = 15 + int((months_covered - 3) * 5)
            breakdown['emergency_fund']['message'] = f"{months_covered:.1f} months covered. Fair."
        elif months_covered > 0:
            breakdown['emergency_fund']['score'] = int(months_covered * 5)
            breakdown['emergency_fund']['message'] = f"{months_covered:.1f} months covered. Needs work."
        else:
            breakdown['emergency_fund']['message'] = "No emergency fund."
    
    # 2. Savings Rate (30 pts)
    # Logic: (Total Income - Pure Expenses) / Total Income
    if total_income > 0:
        savings_rate = (total_income - pure_expenses) / total_income
        if savings_rate >= 0.20:
            breakdown['savings_rate']['score'] = 30
            breakdown['savings_rate']['message'] = f"Saving {savings_rate*100:.1f}%. Excellent!"
        elif savings_rate >= 0.10:
            breakdown['savings_rate']['score'] = 15 + int((savings_rate - 0.10) * 150)
            breakdown['savings_rate']['message'] = f"Saving {savings_rate*100:.1f}%. Fair."
        elif savings_rate > 0:
            breakdown['savings_rate']['score'] = int(savings_rate * 150)
            breakdown['savings_rate']['message'] = f"Saving {savings_rate*100:.1f}%. Needs work."
        else:
            breakdown['savings_rate']['message'] = "Spending more than earning."
            
    # 3. Budget Adherence (20 pts)
    today = datetime.utcnow()
    current_month_budgets = [b for b in user.budgets if b.month == today.month and b.year == today.year]
    if current_month_budgets:
        total_budget = sum(b.amount for b in current_month_budgets if b.category != 'Overall')
        overall = next((b.amount for b in current_month_budgets if b.category == 'Overall'), None)
        total_budget = overall if overall else total_budget
        
        current_expenses = sum(e.amount for e in user.expenses if e.date.month == today.month and e.date.year == today.year and e.category not in ['Investment', 'Savings Goal'])
        
        if total_budget > 0:
            ratio = current_expenses / total_budget
            if ratio <= 1.0:
                breakdown['budget_adherence']['score'] = 20
                breakdown['budget_adherence']['message'] = "Under budget. Excellent!"
            elif ratio <= 1.2:
                breakdown['budget_adherence']['score'] = int(20 - ((ratio - 1.0) * 100))
                breakdown['budget_adherence']['message'] = "Slightly over budget."
            else:
                breakdown['budget_adherence']['message'] = "Significantly over budget."
    else:
        breakdown['budget_adherence']['message'] = "No budget set for this month."
        
    # 4. Investment & Goal Focus (20 pts)
    total_invested = sum(inv.total_invested() for inv in user.investments)
    total_goals = sum(g.current_amount for g in user.goals)
    total_active_money = total_invested + total_goals
    
    # Net worth = Available Cash + Active Money
    available_savings = user.get_available_savings()
    net_worth = available_savings + total_active_money 
    
    if net_worth > 0:
        focus_ratio = total_active_money / net_worth
        if focus_ratio >= 0.50:
            breakdown['investment_focus']['score'] = 20
            breakdown['investment_focus']['message'] = f"{focus_ratio*100:.0f}% of wealth deployed. Excellent!"
        elif focus_ratio > 0:
            breakdown['investment_focus']['score'] = int(focus_ratio * 40)
            breakdown['investment_focus']['message'] = f"{focus_ratio*100:.0f}% deployed. Room to grow."
        else:
            breakdown['investment_focus']['message'] = "No money invested or saved in goals."

    # Calculate total
    for key in breakdown:
        score += breakdown[key]['score']
        
    return {
        'total_score': score,
        'breakdown': breakdown
    }
