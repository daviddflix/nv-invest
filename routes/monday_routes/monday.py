from datetime import datetime
from scheduler import scheduler
from flask import Blueprint, request
from bots.monday_bot import activate_nv_invest_bot


monday_bp = Blueprint('monday', __name__)


@monday_bp.route('/', methods=['POST'])
def index():
    try:
        command = request.args.get('command')
        if command == 'activate':
            activate_nv_invest_bot()
            # scheduler.add_job(activate_nv_invest_bot, 'interval', id='nv invest', hours=4, next_run_time=datetime.now(), replace_existing=True)
            return 'NV Invest Bot activated', 200
        elif command == 'deactivate':
            scheduler.remove_job(job_id='nv invest')
            return 'NV Invest Bot deactivated', 200
        else:
            return 'Command not valid', 400
    except Exception as e:
        return str(e), 500
    

