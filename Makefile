dev:
	cd app && \
	uvicorn main:app --reload --host 0.0.0.0

prod:
	cd app && \
	uvicorn main:app --host 0.0.0.0