import uuid
from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, 
    ForeignKey, DateTime, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    diaries = relationship("Diary", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    city = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pois = relationship("POI", back_populates="location", cascade="all, delete-orphan")
    foods = relationship("Food", back_populates="location", cascade="all, delete-orphan")
    diaries = relationship("Diary", back_populates="location", cascade="all, delete-orphan")

class POI(Base):
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    latitude = Column(DECIMAL(10, 7))
    longitude = Column(DECIMAL(10, 7))

    # Relationships
    location = relationship("Location", back_populates="pois")
    
class Road(Base):
    __tablename__ = "roads"

    id = Column(Integer, primary_key=True, index=True)
    start_poi_id = Column(Integer, ForeignKey("pois.id", ondelete="CASCADE"), nullable=False)
    end_poi_id = Column(Integer, ForeignKey("pois.id", ondelete="CASCADE"), nullable=False)
    distance = Column(DECIMAL(8, 2), nullable=False)
    crowd_level = Column(Integer, default=1)
    transport_modes = Column(JSON) # 储存数组如: ["walk", "bike"]

    # Relationships
    start_poi = relationship("POI", foreign_keys=[start_poi_id])
    end_poi = relationship("POI", foreign_keys=[end_poi_id])

class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    poi_id = Column(Integer, ForeignKey("pois.id", ondelete="SET NULL"))
    name = Column(String(100), nullable=False)
    price_range = Column(String(50))
    rating = Column(DECIMAL(3, 2), default=0.0)

    # Relationships
    location = relationship("Location", back_populates="foods")
    poi = relationship("POI") # optional relation

class Diary(Base):
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    # 储存哈夫曼压缩二进制串与字典
    compressed_content = Column(Text)
    huffman_map = Column(JSON) 
    
    images = Column(JSON, default=list) # URL列表
    video_path = Column(String(255))
    views = Column(Integer, default=0, index=True)
    rating = Column(DECIMAL(3, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    author = relationship("User", back_populates="diaries")
    location = relationship("Location", back_populates="diaries")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    rating = Column(Integer)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    author = relationship("User", back_populates="comments")

