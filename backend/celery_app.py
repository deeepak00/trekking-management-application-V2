import os
from celery import Celery
from celery.schedules import crontab
from app import app as flask_app_instance

def create_celery_application(flask_application):
    """
    Initializes and configures the Celery application.
    Integrates with the Flask app context so that tasks can interact with the
    database models and the mail configuration.
    """
    # Create the Celery instance using Flask's import name
    celery_application = Celery(flask_application.import_name)

    # Use conf.update to properly configure Celery
    celery_application.conf.update(
        broker_url=flask_application.config.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/1'),
        result_backend=flask_application.config.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/1'),
        timezone='Asia/Kolkata',
        beat_schedule={
            'send-daily-trek-reminders': {
                'task': 'tasks.run_daily_reminders_task',
                # Runs daily at 8:00 AM
                'schedule': crontab(hour=8, minute=0),
            },
            'generate-monthly-report': {
                'task': 'tasks.run_monthly_report_task',
                # Runs on the 1st of every month at 6:00 AM
                'schedule': crontab(day_of_month=1, hour=6, minute=0),
            },
        }
    )

    # Set as default Celery application for this process
    celery_application.set_default()

    # Subclass Celery Task to automatically run tasks inside Flask's application context
    class FlaskContextTask(celery_application.Task):
        def __call__(self, *args, **kwargs):
            with flask_application.app_context():
                return self.run(*args, **kwargs)

    celery_application.Task = FlaskContextTask
    return celery_application

# Create the Celery instance configured with the Flask application
celery_instance = create_celery_application(flask_app_instance)

# Import tasks module to register Celery tasks with the celery_instance
import tasks
