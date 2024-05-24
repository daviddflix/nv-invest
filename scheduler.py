import pytz
from config import db_url
from datetime import datetime
from config import Session, Bot, Error
from services.monday.actions import create_notification
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES, EVENT_JOB_EXECUTED

david_user_id = 53919924
DEX_board_id = 1355568860

scheduler = BackgroundScheduler(executors={'default': {'type': 'threadpool', 'max_workers': 10}})
scheduler.add_jobstore('sqlalchemy', url= db_url)

if scheduler.state != 1:
    scheduler.start()
    print('-----Scheduler started-----')

def job_executed(event): 
    try:
        job_id = str(event.job_id).capitalize()
        with Session() as session:
            nv_invest_bot = session.query(Bot).filter_by(name=str(event.job_id)).first()
            if nv_invest_bot:
                london_timezone = pytz.timezone('Europe/London')
                current_time_uk = datetime.now(london_timezone)
                nv_invest_bot.updated_at = current_time_uk
                session.commit()
            print(f'\n{job_id} was executed successfully at {event.scheduled_run_time}, response: {event.retval}')
      
    except Exception as e:
        session.rollback()
        print(f'Error updating datetime for NV Invest Bot. {str(e)}')
    
    
def job_error(event):
    try:
        message = f'An error occured in {event.job_id}, response: {event.retval}'
        create_notification(user_id=david_user_id, item_id=DEX_board_id, value=message)
        print(message)
    except Exception as e:
        print(f'Error executing NV Invest Bot. Error: {str(e)}')
   

def job_max_instances_reached(event): 
    try:
        message = f'Maximum number of running instances reached, *Upgrade* the time interval for {event.job_id}'  
        create_notification(user_id=david_user_id, item_id=DEX_board_id, value=message)
        print(message)
    except Exception as e:
        print(f'Maximum number of running instances reached. Error: {str(e)}')

  

   
scheduler.add_listener(job_error, EVENT_JOB_ERROR)
scheduler.add_listener(job_max_instances_reached, EVENT_JOB_MAX_INSTANCES)
scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)