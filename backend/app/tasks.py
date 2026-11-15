import asyncio
from datetime import datetime, timedelta, timezone

from .database import SessionLocal
from .models import AdminReminderLog, Order


async def check_stale_orders_loop():
    db = None
    while True:
        try:
            db = SessionLocal()
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
            stale_orders = db.query(Order).filter(
                Order.status.in_(["PLACED", "ACCEPTED"]),
                Order.updated_at <= cutoff,
            ).all()

            for order in stale_orders:
                existing = db.query(AdminReminderLog).filter(
                    AdminReminderLog.order_id == order.id,
                    AdminReminderLog.is_resolved.is_(False),
                ).first()
                if not existing:
                    reminder = AdminReminderLog(
                        order_id=order.id,
                        restaurant_id=order.restaurant_id,
                        message=f"Alert: Order #{order.id} has remained in '{order.status}' status for over 15 minutes.",
                    )
                    db.add(reminder)
            db.commit()
        except Exception as exc:
            print(f"[Background Task Error] {exc}")
        finally:
            if db is not None:
                db.close()

        await asyncio.sleep(60)
