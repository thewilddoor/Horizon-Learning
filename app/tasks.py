from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.utils import generate_daily_reports
from app.models import Message, Report
from app import db

def delete_old_messages():
    """Deletes messages older than 24 hours after report generation."""
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    old_messages = Message.query.filter(Message.timestamp < cutoff_time).all()
    for message in old_messages:
        db.session.delete(message)
    db.session.commit()
    print(f"Deleted {len(old_messages)} messages older than {cutoff_time}.")


def reset_weekly_reports():
    """Resets report data weekly by deleting reports older than a week."""
    cutoff_date = datetime.utcnow().date() - timedelta(weeks=1)
    old_reports = Report.query.filter(Report.date < cutoff_date).all()
    for report in old_reports:
        db.session.delete(report)
    db.session.commit()
    print(f"Deleted {len(old_reports)} reports older than {cutoff_date}.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Schedule daily report generation at 00:30 UTC (if applicable)
    scheduler.add_job(
        func=generate_daily_reports,
        trigger='cron',
        hour=0,
        minute=30,
        id='daily_report_generation',
        replace_existing=True
    )
    
    # Schedule message cleanup at 00:00 UTC daily
    scheduler.add_job(
        func=delete_old_messages,
        trigger='cron',
        hour=0,
        minute=0,
        id='daily_message_cleanup',
        replace_existing=True
    )
    
    # Optionally, schedule weekly report reset
    scheduler.add_job(
        func=reset_weekly_reports,
        trigger='cron',
        day_of_week='mon',
        hour=1,
        minute=0,
        id='weekly_report_reset',
        replace_existing=True
    )
    
    scheduler.start()
    print("Scheduler started.")

    # Shut down the scheduler when exiting the app
    import atexit
    atexit.register(lambda: scheduler.shutdown())


