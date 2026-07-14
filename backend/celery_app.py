import os
from celery import Celery
from celery.schedules import crontab
from app import app as flask_app_instance

def create_celery_application(flask_application):
    celery_application = Celery(flask_application.import_name)

    celery_application.conf.update(
        broker_url=flask_application.config.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/1'),
        result_backend=flask_application.config.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/1'),
        timezone='Asia/Kolkata',
        beat_schedule={
            'send-daily-trek-reminders': {
                'task': 'tasks.run_daily_reminders_task',
                'schedule': crontab(hour=8, minute=0),
            },
            'generate-monthly-report': {
                'task': 'tasks.run_monthly_report_task',
                'schedule': crontab(day_of_month=1, hour=6, minute=0),
            },
        }
    )

    celery_application.set_default()

    class FlaskContextTask(celery_application.Task):
        def __call__(self, *args, **kwargs):
            with flask_application.app_context():
                return self.run(*args, **kwargs)

    celery_application.Task = FlaskContextTask
    return celery_application


celery_instance = create_celery_application(flask_app_instance)


import tasks
