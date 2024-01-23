from datetime import datetime
from scheduler import scheduler
from flask import Blueprint, request
from bots.monday_bot import activate_bot


monday_bp = Blueprint('monday', __name__)


@monday_bp.route('/', methods=['POST'])
def index():
    try:
        command = request.args.get('command')
        if command == 'activate':
            # activate_bot()
            scheduler.add_job(activate_bot, 'interval', id='nv invest', hours=4, next_run_time=datetime.now(), replace_existing=True)
            return 'NV Invest Bot activated'
        elif command == 'deactivate':
            scheduler.remove_job(job_id='nv invest')
            return 'NV Invest Bot deactivated'
        else:
            return 'Command not valid'
    except Exception as e:
        return str(e)