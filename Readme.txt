запуск api через команду:
uvicorn main:app --reload

UI Swagger: http://127.0.0.1:8000/docs

Очистка кэшов 
Remove-Item -Recurse -Force __pycache__, tests\__pycache__