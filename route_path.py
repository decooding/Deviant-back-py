from main import app

print("📌 Доступные маршруты в FastAPI:")
for route in app.routes:
    print(route.path, route.methods)
