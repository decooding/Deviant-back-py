from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def get_alerts(self):
        self.client.get("/alerts/")
