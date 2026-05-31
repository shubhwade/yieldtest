import os
import sys

# Add the current directory to sys.path to ensure imports work correctly in Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.market_routes import market_bp
from routes.news_routes import news_bp
from routes.treasury_routes import treasury_bp
from routes.bonds_routes import bonds_bp
from routes.portfolio_routes import portfolio_bp
from routes.analytics_routes import analytics_bp
from routes.ai_routes import ai_bp
from routes.screener_routes import screener_bp
from routes.macro_routes import macro_bp
from routes.watchlist_routes import watchlist_bp
from routes.alerts_routes import alerts_bp
from routes.search_routes import search_bp
from routes.telemetry_routes import telemetry_bp
from routes.backtest_routes import backtest_bp
from routes.fred_routes import fred_bp
from routes.credit_routes import credit_bp

app = Flask(__name__)
CORS(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(market_bp)
app.register_blueprint(news_bp)
app.register_blueprint(treasury_bp)
app.register_blueprint(bonds_bp)
app.register_blueprint(portfolio_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(screener_bp)
app.register_blueprint(macro_bp)
app.register_blueprint(watchlist_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(search_bp)
app.register_blueprint(telemetry_bp)
app.register_blueprint(backtest_bp)
app.register_blueprint(fred_bp)
app.register_blueprint(credit_bp)

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "platform": "vercel-serverless"})

# Vercel requires the app instance to be named 'app'
if __name__ == "__main__":
    app.run()
