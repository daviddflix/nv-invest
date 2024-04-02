from flask import Flask
from routes.monday_routes.monday import monday_bp
from routes.nv_invest_bot_routes.nv_bot import nv_invest_bot_bp

app = Flask(__name__)
app.name = 'NV Invest Bot'


app.register_blueprint(monday_bp)
app.register_blueprint(nv_invest_bot_bp)
    
    
if __name__ == '__main__':
    try:
        print('---Novatide server is running---') 
        app.run(debug=False, use_reloader=False, port=6000) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")
    finally:
        print('---AI Alpha server was stopped---')
    
