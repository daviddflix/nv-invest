from datetime import datetime
from scheduler import scheduler
from flask import Blueprint, request, jsonify
from bots.monday_bot import activate_nv_invest_bot
from werkzeug.exceptions import BadRequest
from config import session, Board

monday_bp = Blueprint('monday', __name__)

# Activates the Monday Bot
@monday_bp.route('/activate/nv_bot', methods=['POST'])
def index():
    try:
        command = request.args.get('command')
        if command == 'activate':
            # activate_nv_invest_bot()
            scheduler.add_job(activate_nv_invest_bot, 'interval', id='nv invest', hours=4, next_run_time=datetime.now(), replace_existing=True)
            return 'NV Invest Bot activated', 200
        elif command == 'deactivate':
            scheduler.remove_job(job_id='nv invest')
            return 'NV Invest Bot deactivated', 200
        else:
            return 'Command not valid', 400
    except Exception as e:
        return str(e), 500


# Adds a new Monday.com Board
@monday_bp.route('/add_board', methods=['POST'])
def add_new_monday_board():
    try:
        data = request.json

        if 'board_name' not in data or 'board_id' not in data:
            raise BadRequest("Both 'board_name' and 'board_id' are required.")

        if not isinstance(data['board_name'], str) or not isinstance(data['board_id'], int):
            raise BadRequest("Invalid data types. 'board_name' should be a string, and 'board_id' should be an integer.")

        board_name = data['board_name'].casefold().strip()
        board_id = data['board_id']

        existing_board = session.query(Board).filter_by(board_name=board_name, monday_board_id=board_id).first()
        if not existing_board:
            new_board = Board(
                board_name=board_name, monday_board_id=board_id
            )
            session.add(new_board)
            session.commit()
            return jsonify({'message': 'New board added', 'status': 200}), 200
        else:
            return jsonify({'message': 'Board already exists', 'status': 409, 'existing_board': existing_board.as_dict()}), 409

    except BadRequest as e:
        return jsonify({'error': str(e), 'status': 400}), 400
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e), 'status': 500}), 500


# Delete a Monday.com Board
@monday_bp.route('/delete_board/<int:board_id>', methods=['DELETE'])
def delete_monday_board(board_id):
    try:
        board_to_delete = session.query(Board).filter_by(monday_board_id=board_id).first()

        if not board_to_delete:
            return jsonify({'message': 'Board not found', 'status': 404}), 404

        session.delete(board_to_delete)
        session.commit()

        return jsonify({'message': 'Board deleted successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e), 'status': 500}), 500


# Edit a Monday.com Board (JUST THE NAME)
@monday_bp.route('/edit_board/<int:board_id>', methods=['PUT'])
def edit_monday_board(board_id):
    try:
        data = request.json

        if 'board_name' not in data:
            raise BadRequest(" 'board_name' is required for editing.")

        if not isinstance(data['board_name'], str):
            raise BadRequest("'board_name' should be a string.")

        board_to_edit = session.query(Board).filter_by(monday_board_id=board_id).first()

        if not board_to_edit:
            return jsonify({'message': 'Board not found', 'status': 404}), 404

        board_to_edit.board_name = data['board_name'].casefold().strip()
        session.commit()

        return jsonify({'message': 'Board name edited successfully', 'status': 200}), 200

    except BadRequest as e:
        return jsonify({'error': str(e), 'status': 400}), 400
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e), 'status': 500}), 500


# Get all Monday.com Boards
@monday_bp.route('/get_all_boards', methods=['GET'])
def get_all_monday_boards():
    try:
        all_boards = session.query(Board).all()
        boards_list = [board.as_dict() for board in all_boards]

        return jsonify({'boards': boards_list, 'status': 200}), 200

    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500
