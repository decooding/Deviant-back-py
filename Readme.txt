запуск api через команду:
uvicorn main:app --reload

UI Swagger: http://127.0.0.1:8000/docs

Вход в БД:
docker ps
docker exec -it cb1f942209c4 psql -U admin -d video_analysis  

Запусти Prometheus в Docker:
docker run -d --name prometheus -p 9090:9090 -v "D:/Github/Deviant-back-py/prometheus.yml:/etc/prometheus/prometheus.yml" prom/prometheus
Теперь Prometheus доступен по адресу:
👉 http://localhost:9090

Запусти Grafana:
docker run -d --name grafana -p 3000:3000 grafana/grafana
docker start grafana
http://localhost:3000

Очистка кэшов 
Remove-Item -Recurse -Force __pycache__, tests\__pycache__




-----------------------------------------------------------------------
Collab: https://colab.research.google.com/drive/1eA51eo34-KlHbp8vqg-8SFURGi1Jojo2#scrollTo=LHeG9Ju7yaHr

