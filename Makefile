dev:
	uvicorn main:app --reload --host 0.0.0.0 

prod:
	uvicorn main:app --host 0.0.0.0 