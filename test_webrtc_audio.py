import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import av
import time
import numpy as np

class SimpleAudioTestProcessor(AudioProcessorBase):
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        print(f"SimpleAudioTestProcessor.recv() CALLED at {time.strftime('%H:%M:%S')}, samples: {frame.samples}, rate: {frame.sample_rate}, format: {frame.format.name}", flush=True)
        # Попробуем просто получить данные, чтобы проверить, нет ли тут ошибки
        try:
            data = frame.to_ndarray()
            print(f"  Data shape: {data.shape}, dtype: {data.dtype}", flush=True)
        except Exception as e:
            print(f"  Error converting frame to ndarray: {e}", flush=True)
        return frame

st.title("Тест WebRTC Аудио")

ctx = webrtc_streamer(
    key="audiotest",
    mode=WebRtcMode.RECVONLY,
    audio_processor_factory=SimpleAudioTestProcessor,
    media_stream_constraints={"video": False, "audio": True}
)

if ctx.state.playing:
    st.success("Микрофон должен быть активен. Проверьте консоль сервера.")
else:
    st.info("Нажмите Start в компоненте WebRTC.")