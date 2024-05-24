from config import Bot, Session
from scheduler import scheduler
from flask import Blueprint, jsonify, request
from bots.monday_bot import activate_nv_invest_bot
from bots.monitor_S_R_lines_bot import monday_monitor_prices

nv_invest_bot_bp = Blueprint('nv_invest_bot', __name__)

# Get all existing bots.
@nv_invest_bot_bp.route('/bots', methods=['GET'])
def get_bots():
    try:
        with Session() as session:
            bots = session.query(Bot).all()
            bot_list = []

            for bot in bots:
                bot_dict = bot.as_dict()
                bot_errors = bot.errors
                bot_dict['errors'] = bot_errors
                job = scheduler.get_job(bot.name)
                bot_dict['next_run_time'] = None
                if job:
                    bot_dict['next_run_time'] = job.next_run_time
                bot_list.append(bot_dict)

            return jsonify({'bots': bot_list}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


# Activates the Monday Bot
@nv_invest_bot_bp.route('/activate/nv_bot', methods=['POST'])
def index():
    try:
        command = request.args.get('command')
        bot_id = request.args.get('bot_id')

        with Session() as session:
            if command == 'activate':

                nv_invest_bot = session.query(Bot).filter_by(id=bot_id).first()
                if not nv_invest_bot:
                    return 'No Bot found to activate', 404
                
                if nv_invest_bot.status:
                    return 'Bot is already active', 200
                
                function_to_schedule = activate_nv_invest_bot
                if nv_invest_bot.name == 'nv invest - monitor':
                    function_to_schedule = monday_monitor_prices
                
                scheduler.add_job(function_to_schedule, 'interval', id=nv_invest_bot.name, hours=nv_invest_bot.interval, replace_existing=True)
                nv_invest_bot.status = True
                session.commit()
                return 'NV Invest Bot activated', 200
            elif command == 'deactivate':

                nv_invest_bot = session.query(Bot).filter_by(id=bot_id).first()
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
        session.rollback()
        return str(e), 500
    

