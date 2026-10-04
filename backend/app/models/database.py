import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Text, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 数据库路径（从 .env 读取，默认 ./data/papers.db）
DB_PATH = os.getenv("SQLITE_PATH", "./data/papers.db")

# 确保目录存在
os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)

# 创建 engine，开启 WAL 模式提升并发读写性能
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False
)

# 开启 WAL 模式
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Paper(Base):
    """论文元数据表"""
    __tablename__ = "papers"

    id = Column(String, primary_key=True)          # UUID
    title = Column(String, nullable=True)          # 论文标题
    authors = Column(Text, nullable=True)          # 作者列表（JSON 字符串）
    abstract = Column(Text, nullable=True)         # 摘要
    file_path = Column(String, nullable=True)      # PDF 原文件路径
    markdown_path = Column(String, nullable=True)  # 解析后的 Markdown 路径
    version = Column(String, nullable=True)        # 版本号（如 v1、v7）
    page_count = Column(Integer, nullable=True)    # 页数
    parse_mode = Column(String, nullable=True)     # flash / precise
    created_at = Column(DateTime, default=datetime.utcnow)


class Chunk(Base):
    """论文分块表（用于 RAG 检索）"""
    __tablename__ = "chunks"

    id = Column(String, primary_key=True)          # chunk UUID
    paper_id = Column(String, index=True)          # 关联的论文 ID
    content = Column(Text)                         # chunk 文本内容
    section_path = Column(String, nullable=True)   # 章节路径（如 "3.2 Attention"）
    page_number = Column(Integer, nullable=True)   # 页码
    chunk_index = Column(Integer, nullable=True)   # 在论文中的序号
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """创建所有表"""
    Base.metadata.create_all(engine)
    print(f"[Database] 表已创建，数据库路径: {DB_PATH}")


if __name__ == "__main__":
    init_db()