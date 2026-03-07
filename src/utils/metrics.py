from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware 
import time


# Define metrics
REQUEST_COUNT = Counter("http_requests_total","Total HTTP Requests", ["method","endpoint","status"])
REQUEST_LATENCY = Histogram("http_request_duaration_seconds","HTTP Request Latency",["method","endpoint"])

class PrometheuMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        start_time= time.time()
        
        response = await call_next(request)
        
        duration= time.time()-start_time
        endpoint = request.url.path
        
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(duration)
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
        
        return response
    
def setup_metrics(app:FastAPI):
    """
    setup promethus metrics middleware and endpoint
    """
    
    # Add prometheus middleware
    app.add_middleware(PrometheuMiddleware)
    
    @app.get("/Trave_sda_5fefex",include_in_schema=False)
    def metrics():
        return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)