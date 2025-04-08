# api/__init__.py
"""
API endpoints package.
"""
from api.upload import register_upload_routes
from api.preprocess import register_preprocess_routes
from api.generation import register_generation_routes
from api.filters import register_filter_routes
from api.metrics import register_metrics_routes