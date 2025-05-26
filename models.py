# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base # Сіздің database.py файлыңыздан Base импорты

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="Пайдаланушының бірегей идентификаторы")
    username = Column(String(100), unique=True, nullable=False, index=True, comment="Пайдаланушының логині (бірегей)")
    password_hash = Column(String(255), nullable=False, comment="Құпия сөздің хештелген нұсқасы")
    
    # Егер дабылдарды пайдаланушыларға байлағыңыз келсе, бұл қатынасты қосыңыз
    # alerts = relationship("Alert", back_populates="user")
    # video_analysis_results = relationship("VideoAnalysisResult", back_populates="user") 

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, comment="Дабылдың бірегей идентификаторы")
    alert_type = Column(String(100), index=True, nullable=False, comment="Дабылдың түрі (мысалы, 'fall_detected', 'weapon_knife', 'sound_scream')")
    description = Column(Text, nullable=True, comment="Дабылдың толық сипаттамасы")
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True, comment="Дабылдың тіркелген уақыты (автоматты түрде)")
    video_filename = Column(String(255), nullable=True, index=True, comment="Дабылмен байланысты видео файлдың атауы (егер бар болса)")
    details_json = Column(Text, nullable=True, comment="Дабыл туралы қосымша мәліметтер JSON форматында (мысалы, координаттар, сенімділік)")
    
    # Егер дабылды белгілі бір пайдаланушыға байлау керек болса:
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="Дабылды тіркеген немесе оған жауапты пайдаланушының ID-сы")
    # user = relationship("User", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', timestamp='{self.timestamp}')>"

class VideoAnalysisResult(Base):
    __tablename__ = "video_analysis_results"

    id = Column(Integer, primary_key=True, index=True, comment="Видео талдау нәтижесінің бірегей идентификаторы")
    video_filename = Column(String(255), nullable=False, index=True, comment="Талданған видео файлдың атауы")
    analysis_start_time = Column(DateTime(timezone=True), default=func.now(), comment="Талдаудың басталу уақыты")
    analysis_duration_seconds = Column(Integer, nullable=True, comment="Талдауға кеткен уақыт (секундпен)")
    frames_analyzed = Column(Integer, nullable=True, comment="Талданған кадрлар саны")
    is_suspicious = Column(Boolean, default=False, nullable=False, comment="Күдікті әрекеттер анықталды ма (True/False)")
    detected_events_summary = Column(Text, nullable=True, comment="Анықталған оқиғалардың қысқаша мазмұны (оқылатын форматта)")
    raw_results_json = Column(Text, nullable=True, comment="Талдаудың толық нәтижелері JSON форматында (барлық анықталған оқиғалар, уақыт белгілері, сенімділік деңгейлері)")
    
    # Егер талдауды белгілі бір пайдаланушы бастаса:
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="Талдауды бастаған пайдаланушының ID-сы")
    # user = relationship("User", back_populates="video_analysis_results")

    def __repr__(self):
        return f"<VideoAnalysisResult(id={self.id}, video_filename='{self.video_filename}', suspicious={self.is_suspicious})>"