from config import db_url
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
    job_id = str(event.job_id).capitalize()
    print(f'\n{job_id} was executed successfully at {event.scheduled_run_time}, response: {event.retval}')
    
def job_error(event):
    job_id = str(event.job_id).capitalize()
    message = f'An error occured in {job_id}, response: {event.retval}'
    create_notification(user_id=david_user_id, item_id=DEX_board_id, value=message)
    print(message)
   
def job_max_instances_reached(event): 
    job_id = str(event.job_id).capitalize()
    message = f'Maximum number of running instances reached, *Upgrade* the time interval for {job_id}'  
    create_notification(user_id=david_user_id, item_id=DEX_board_id, value=message)
    print(message)

  

   
scheduler.add_listener(job_error, EVENT_JOB_ERROR)
scheduler.add_listener(job_max_instances_reached, EVENT_JOB_MAX_INSTANCES)
scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)