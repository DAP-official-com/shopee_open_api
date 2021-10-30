from shopee_open_api.scheduled_tasks.tasks import update_products


def cron():
    update_products()
