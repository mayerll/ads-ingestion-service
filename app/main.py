import asyncio
import json
import logging
import os
import time
import uuid
from typing import List

from fastapi import FastAPI, Request, HTTPException
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

app = FastAPI()

QUEUE_MAXSIZE = int(os.getenv("QUEUE_MAXSIZE", "10000"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
BATCH_TIMEOUT = float(os.getenv("BATCH_TIMEOUT", "0.5"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion")

REQUEST_COUNT = Counter("ingest_requests_total", "Total ingestion requests")
REQUEST_LATENCY = Histogram("ingest_request_latency_seconds", "Request latency")
QUEUE_DEPTH = Gauge("ingest_queue_depth", "Queue depth")
BATCH_COUNT = Counter("kafka_batch_total", "Kafka batches sent")
FAILED_BATCH_COUNT = Counter("kafka_batch_failed_total", "Failed Kafka batches")

queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
shutdown_event = asyncio.Event()

class KafkaProducerInterface:
    async def send_batch(self, batch: List[dict]):
        await asyncio.sleep(0.01)

producer = KafkaProducerInterface()

@app.post("/ingest")
async def ingest(request: Request):
    start = time.time()
    REQUEST_COUNT.inc()

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    request_id = str(uuid.uuid4())

    if queue.full():
        raise HTTPException(status_code=429, detail="Queue full")

    await queue.put({
        "request_id": request_id,
        "payload": payload,
        "timestamp": time.time()
    })

    QUEUE_DEPTH.set(queue.qsize())

    latency = time.time() - start
    REQUEST_LATENCY.observe(latency)

    logger.info(json.dumps({
        "event": "ingest",
        "request_id": request_id,
        "latency_ms": int(latency * 1000)
    }))

    return {"status": "accepted", "request_id": request_id}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")


async def kafka_worker():
    while not shutdown_event.is_set():
        batch = []
        start_time = time.time()

        while len(batch) < BATCH_SIZE:
            timeout = BATCH_TIMEOUT - (time.time() - start_time)
            if timeout <= 0:
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=timeout)
                batch.append(item)
            except asyncio.TimeoutError:
                break

        if batch:
            try:
                await producer.send_batch(batch)
                BATCH_COUNT.inc()
            except Exception as e:
                FAILED_BATCH_COUNT.inc()
                logger.error(f"Kafka batch failed: {e}")

        QUEUE_DEPTH.set(queue.qsize())


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(kafka_worker())


@app.on_event("shutdown")
async def shutdown_event_handler():
    shutdown_event.set()
    logger.info("Shutting down gracefully...")
