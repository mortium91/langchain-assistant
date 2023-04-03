dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

prod:
	uvicorn main:app --host 0.0.0.0 --port 8000