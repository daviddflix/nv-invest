from flask import Blueprint, request, jsonify
from bots.monitor_S_R_lines_bot import monday_monitor_prices
from config import Session
from scheduler import scheduler, Bot

monday_monitor_bp = Blueprint('monday_monitor_bp', __name__)


# Activates the Monitor monday prices
@monday_monitor_bp.route('/nv_bot_monitor', methods=['POST'])
def index():
    try:
        command = request.args.get('command')
        with Session() as session:
            if command == 'activate':
                nv_invest_bot = session.query(Bot).filter_by(name="nv invest - monitor").first()
                if not nv_invest_bot:
                    return 'No Bot found to activate', 404
                
                if nv_invest_bot.status:
                    return 'Bot is already active', 200
                
                # scheduler.add_job(monday_monitor_prices, 'interval', id=nv_invest_bot.name, minutes=4, replace_existing=True)
                scheduler.add_job(monday_monitor_prices, 'interval', id=nv_invest_bot.name, hours=nv_invest_bot.interval, replace_existing=True)
                nv_invest_bot.status = True
                session.commit()
                return 'NV Invest Bot activated', 200
            elif command == 'deactivate':
                nv_invest_bot = session.query(Bot).filter_by(name="nv invest - monitor").first()
                if not nv_invest_bot:
                    return 'No Bot found to deactivate', 404
                
                if nv_invest_bot.status == False:
                    return 'Bot is already inactive', 200
                
                scheduler.remove_job(job_id=nv_invest_bot.name)
                nv_invest_bot.status = False
                session.commit()
                return 'NV Invest Bot deactivated', 200
            else:
                return 'Command not valid', 400
    except Exception as e:
        return str(e), 500
