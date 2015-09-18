from celery import Celery


app = Celery(
    'clinton',
    broker='amqp://',
    backend='amqp://',
    include=['clinton.tasks']
)

app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=60,
)
