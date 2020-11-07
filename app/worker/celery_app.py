import os

from celery import Celery

celery_app = None

if not bool(os.getenv('DOCKER')): # if running example without docker
    celery_app = Celery(
        "worker",
        backend="redis://:password123@localhost:6379/0",  # no docker, all is localhost
        broker="amqp://user:bitnami@localhost:5672//"
    )
    celery_app.conf.task_routes = {
        "app.worker.celery_worker.test_celery": "test-queue",
        "app.worker.celery_worker.tsk_start_tracking_all": "tsk_start_tracking_all",
        "app.worker.celery_worker.tsk_track_category": "tsk_track_category"
        
        
        }
else: # running example with docker
    celery_app = Celery(
        "worker",
        backend="redis://:password123@redis:6379/0",  # named service hosts
        broker="amqp://user:bitnami@rabbitmq:5672//"
    )
    celery_app.conf.task_routes = {
        "app.app.worker.celery_worker.test_celery": "test-queue",
        "app.app.worker.celery_worker.tsk_start_tracking_all": "tsk_start_tracking_all",
        "app.app.worker.celery_worker.tsk_track_category": "tsk_track_category"
        }

celery_app.conf.update(task_track_started=True)


def make_task_name(task_suffix):
    task_name = None
    # set correct task name based on the way you run the example
    if not bool(os.getenv('DOCKER', 'False')):
        task_name = "app.worker.celery_worker"
    else:
        task_name = "app.app.worker.celery_worker"

    return task_name + f'.{task_suffix}'