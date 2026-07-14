import sys
from app import app
import tasks

if len(sys.argv) < 2:
    print("Usage: python trigger.py [reminders|report]")
    sys.exit(1)

task_type = sys.argv[1].lower()

with app.app_context():
    if task_type == "reminders":
        print("Triggering daily reminders task...")
        res = tasks.run_daily_reminders_task()
        print(res)
    elif task_type == "report":
        print("Triggering monthly report task...")
        res = tasks.run_monthly_report_task()
        print(res)
    else:
        print("Invalid option. Choose 'reminders' or 'report'.")
