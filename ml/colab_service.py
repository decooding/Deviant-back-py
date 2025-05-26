import requests

def send_video_to_colab(video_path: str):
    url = "https://83d1ca4edcb327457a.gradio.live/api/predict/"  # <--- Обновляй эту ссылку при новом запуске Colab
    files = {'data': open(video_path, 'rb')}
    response = requests.post(url, files=files)
    
    if response.ok:
        return response.json()
    else:
        return {"error": "Failed to process video"}
