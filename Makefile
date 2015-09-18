clean:
	find . -name '*.pyc' -delete

worker:
	celery -A clinton worker --app=clinton.celery_app:app --loglevel=info
