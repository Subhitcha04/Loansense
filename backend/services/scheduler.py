from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
from sqlalchemy import text


def check_overdue():
    """
    Daily job: marks unpaid EMIs past their due date as 'overdue'
    and fires payment.overdue webhooks.
    Runs at midnight UTC.
    """
    from db.connection import SessionLocal
    from services.webhook_dispatcher import dispatch

    db = SessionLocal()
    try:
        today = date.today()
        result = db.execute(
            text("""
                SELECT id, loan_id, instalment_no, due_date, emi_amount
                FROM repayment_schedules
                WHERE due_date < :today AND status = 'upcoming'
            """),
            {"today": today}
        )
        overdue_rows = result.fetchall()

        for row in overdue_rows:
            db.execute(
                text("UPDATE repayment_schedules SET status='overdue' WHERE id=:id"),
                {"id": row[0]}
            )
            db.commit()

            dispatch("payment.overdue", {
                "loan_id": row[1],
                "instalment_no": row[2],
                "due_date": str(row[3]),
                "emi_amount": float(row[4])
            })

        print(f"[Scheduler] Overdue check complete. Marked {len(overdue_rows)} instalments overdue.")
    except Exception as e:
        print(f"[Scheduler] Error in overdue check: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_overdue, "cron", hour=0, minute=0)
    scheduler.start()
    print("[Scheduler] APScheduler started — overdue check runs daily at midnight UTC.")
    return scheduler
