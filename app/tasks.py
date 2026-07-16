from app import scheduler, db
from app.models import Investment
from datetime import datetime
import yfinance as yf

@scheduler.task('cron', id='update_stock_prices_daily', hour=0, minute=0)
def update_stock_prices_daily():
    """Fetches the latest prices for all investments every midnight."""
    # Flask-APScheduler sets scheduler.app when init_app is called
    with scheduler.app.app_context():
        print(f"[{datetime.utcnow()}] Starting daily stock price update...")
        investments = Investment.query.filter(Investment.symbol != None, Investment.symbol != "").all()
        
        updated_count = 0
        for inv in investments:
            try:
                ticker = yf.Ticker(inv.symbol.strip().upper())
                last_price = ticker.fast_info['lastPrice']
                if last_price and last_price > 0:
                    inv.current_price = float(last_price)
                    inv.last_updated = datetime.utcnow()
                    updated_count += 1
            except Exception as e:
                print(f"Failed to fetch price for {inv.symbol}: {e}")
                
        if updated_count > 0:
            db.session.commit()
            print(f"[{datetime.utcnow()}] Successfully updated {updated_count} investment prices.")
        else:
            print(f"[{datetime.utcnow()}] No investment prices needed updating.")
