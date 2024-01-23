from flask import Flask
from routes.monday_routes.monday import monday_bp

app = Flask(__name__)
app.name = 'NV Invest Bot'


app.register_blueprint(monday_bp)
    
    
if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=6000)
