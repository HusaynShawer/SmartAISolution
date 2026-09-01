from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def init_metrics(app: FastAPI) -> None:
    instrumentator = Instrumentator().instrument(app)
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)