"""
Database models for query logs and metrics
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class QueryLog(Base):
    """Log of search queries"""
    __tablename__ = 'query_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(36), unique=True, nullable=False, index=True)
    query = Column(Text, nullable=False, index=True)
    top_k = Column(Integer)
    alpha = Column(Float)
    normalization = Column(String(50))
    result_count = Column(Integer)
    latency_ms = Column(Float, index=True)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'query': self.query,
            'top_k': self.top_k,
            'alpha': self.alpha,
            'normalization': self.normalization,
            'result_count': self.result_count,
            'latency_ms': self.latency_ms,
            'error': self.error,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Metric(Base):
    """General metrics storage"""
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    labels = Column(Text)  # JSON string of labels
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'labels': json.loads(self.labels) if self.labels else {},
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Database:
    """Database manager"""
    
    def __init__(self, db_path: str = "data/metrics/app.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def log_query(
        self,
        request_id: str,
        query: str,
        top_k: int,
        alpha: float,
        normalization: str,
        result_count: int,
        latency_ms: float,
        error: str = None
    ):
        """Log a search query"""
        session = self.get_session()
        try:
            log = QueryLog(
                request_id=request_id,
                query=query,
                top_k=top_k,
                alpha=alpha,
                normalization=normalization,
                result_count=result_count,
                latency_ms=latency_ms,
                error=error
            )
            session.add(log)
            session.commit()
        finally:
            session.close()
    
    def get_query_stats(self, limit: int = 1000):
        """Get query statistics"""
        session = self.get_session()
        try:
            logs = session.query(QueryLog).order_by(
                QueryLog.timestamp.desc()
            ).limit(limit).all()
            return [log.to_dict() for log in logs]
        finally:
            session.close()
    
    def get_top_queries(self, limit: int = 10):
        """Get most common queries"""
        session = self.get_session()
        try:
            from sqlalchemy import func
            results = session.query(
                QueryLog.query,
                func.count(QueryLog.query).label('count')
            ).group_by(QueryLog.query).order_by(
                func.count(QueryLog.query).desc()
            ).limit(limit).all()
            return [{'query': q, 'count': c} for q, c in results]
        finally:
            session.close()
    
    def get_zero_result_queries(self, limit: int = 10):
        """Get queries that returned no results"""
        session = self.get_session()
        try:
            from sqlalchemy import func
            results = session.query(
                QueryLog.query,
                func.count(QueryLog.query).label('count')
            ).filter(QueryLog.result_count == 0).group_by(
                QueryLog.query
            ).order_by(func.count(QueryLog.query).desc()).limit(limit).all()
            return [{'query': q, 'count': c} for q, c in results]
        finally:
            session.close()
    
    def get_latency_stats(self):
        """Get latency statistics"""
        session = self.get_session()
        try:
            from sqlalchemy import func
            result = session.query(
                func.avg(QueryLog.latency_ms).label('mean'),
                func.min(QueryLog.latency_ms).label('min'),
                func.max(QueryLog.latency_ms).label('max'),
                func.count(QueryLog.id).label('count')
            ).filter(QueryLog.error.is_(None)).first()
            
            if result and result.count > 0:
                # Calculate percentiles
                import numpy as np
                latencies = [log.latency_ms for log in session.query(QueryLog.latency_ms).filter(
                    QueryLog.error.is_(None)
                ).all()]
                
                return {
                    'mean': float(result.mean) if result.mean else 0,
                    'min': float(result.min) if result.min else 0,
                    'max': float(result.max) if result.max else 0,
                    'count': result.count,
                    'p50': float(np.percentile(latencies, 50)),
                    'p95': float(np.percentile(latencies, 95)),
                    'p99': float(np.percentile(latencies, 99))
                }
            return {}
        finally:
            session.close()
