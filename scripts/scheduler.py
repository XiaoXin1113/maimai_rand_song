import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from scripts.update_database import update_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

UTC_8 = timezone('Asia/Shanghai')


async def scheduled_update():
    logger.info("Starting scheduled database update...")
    success = await update_database(force_download=True)
    if success:
        logger.info("Scheduled database update completed successfully")
    else:
        logger.error("Scheduled database update failed")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=UTC_8)
    
    scheduler.add_job(
        scheduled_update,
        CronTrigger(hour=0, minute=0, timezone=UTC_8),
        id='database_update',
        name='Daily database update at 00:00 UTC+8',
        replace_existing=True,
    )
    
    return scheduler


async def run_scheduler():
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started. Database will update daily at 00:00 UTC+8")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(run_scheduler())
