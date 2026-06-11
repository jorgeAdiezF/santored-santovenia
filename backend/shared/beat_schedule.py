from celery import Celery
from celery.schedules import crontab
from .config import get_settings

settings = get_settings()

beat_app = Celery(
    "beat",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

beat_app.conf.beat_schedule = {
    # Refresh materialized view every hour
    "refresh-last-price-view": {
        "task": "beat_tasks.refresh_last_price_view",
        "schedule": crontab(minute=0),
    },
    # Auto-homologate pending lines every 15 minutes
    "auto-homologate-pending": {
        "task": "beat_tasks.auto_homologate_pending",
        "schedule": crontab(minute="*/15"),
    },
}

beat_app.conf.timezone = "Europe/Madrid"


@beat_app.task(name="beat_tasks.refresh_last_price_view")
def refresh_last_price_view():
    """Refresh the last_price_per_material materialized view."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    async def _run():
        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.execute(
                text("REFRESH MATERIALIZED VIEW CONCURRENTLY last_price_per_material")
            )
        await engine.dispose()

    asyncio.run(_run())
    return {"status": "refreshed", "view": "last_price_per_material"}


@beat_app.task(name="beat_tasks.auto_homologate_pending")
def auto_homologate_pending():
    """Trigger auto-homologation for all pending invoice lines."""
    beat_app.send_task(
        "homologation_worker.process_invoice_lines",
        args=[None, []],
        kwargs={"all_pending": True},
        queue="homologation",
    )
    return {"status": "triggered"}
