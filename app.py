from flask import Flask, request
from scheduler import scheduler
from bot import activate_bot
from datetime import datetime

app = Flask(__name__)
app.name = 'NV Invest Bot'

@app.route('/', methods=['POST'])
def index():
    try:
        command = request.args.get('command')
        if command == 'activate':
            scheduler.add_job(activate_bot, 'interval', id='nv invest', days=1, next_run_time=datetime.now(), replace_existing=True)
            return 'NV Invest Bot activated'
        elif command == 'deactivate':
            scheduler.remove_job(job_id='nv invest')
            return 'NV Invest Bot deactivated'
        else:
            return 'Command not valid'
    except Exception as e:
        return str(e)
    
    
if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=6000)
