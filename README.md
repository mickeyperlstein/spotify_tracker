# Spotify tracking app with celery tasks

> Tracking app for playlists by categories .

## Requirements

- Docker
  - [docker-compose](https://docs.docker.com/compose/install/)

1. Run command ```docker-compose up```to start up the RabbitMQ, Redis, flower and our application/worker instances.
2. Navigate to the [http://localhost:8000/docs](http://localhost:8000/docs) and execute test API call. You can monitor the execution of the celery tasks in the console logs or navigate to the flower monitoring app at [http://localhost:5555](http://localhost:5555) (username: user, password: test).


## requirements:
inside app/spotify_app insert SpotifyAPI key and client secret.
this currently includes my API keys for the free version, I dont use spotify, 
so i dont care if you use/abuse this key 

## Architecture
 > most servers chosen were bitnami servers so everything works together
 1. web server is  FastApi over hypercorn
   -  swagger is at : [http://localhost:8000/docs](http://localhost:8000/docs)
   
 2. celery managed by flower > [http://localhost:5555](http://localhost:5555) 
 user=user, password=test
 > using celery-flower preconfigured image
 - rabbit is celery queue, rabbit managment is at [http://localhost:15672/] user=rabbitmq
 - redis is celery backend
 
 3. Redis 
  - as backend for celery
  - as db for the project 
  - manage with  redisinsight webserver [http://localhost:8001] user=password1  

### Requirements/dependencies

- Python >= 3.8.5
  - [poetry](https://python-poetry.org/docs/#installation)
 
- RabbitMQ instance
- Redis instance


> The RabbitMQ, Redis and flower services can be started with ```docker-compose -f docker-compose-services.yml up```

### Install dependencies

Execute the following command: ```poetry install --dev```

### Run FastAPI app and Celery worker app

1. Start the FastAPI web application with ```poetry run hypercorn app/main:app --reload```.
2. Start the celery worker with command ```poetry run celery worker -A app.worker.celery_worker -l info -Q test-queue -c 1```
3. Navigate to the [http://localhost:8000/docs](http://localhost:8000/docs) and execute test API call. You can monitor the execution of the celery tasks in the console logs or navigate to the flower monitoring app at [http://localhost:5555](http://localhost:5555) (username: user, password: test).

#### Code Architecture
spotify_app:

can be run 