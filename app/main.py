# app/main.py
from fastapi import FastAPI, Request, HTTPException
import logging
import uvicorn
import json
import uuid
import asyncio
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from aiokafka import AIOKafkaProducer

# -------------------
# Logger & Metrics
# -------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ads-ingestion")

REQUEST_COUNT = Counter("ads_ingestion_requests_total", "Total number of ingestion requests")
FAILED_COUNT = Counter("ads_ingestion_failed_total", "Total number of failed ingestion requests")
QUEUE_DEPTH = Gauge("ingest_queue_depth", "Current queue depth")
BATCH_COUNT = Counter("kafka_batch_total", "Kafka batches sent")
FAILED_BATCH_COUNT = Counter("kafka_batch_failed_total", "Kafka batch send failures")

# -------------------
# FastAPI app
# -------------------
app = FastAPI(title="Ads Metrics Ingestion Service")

# -------------------
# Queue & Config
# -------------------
QUEUE_MAXSIZE = 10000
BATCH_SIZE = 500
BATCH_TIMEOUT = 0.5
queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)

KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "ads-metrics"

producer: AIOKafkaProducer = None

# -------------------
# HTTP POST /ingest
# -------------------
@app.post("/ingest")
async def ingest(request: Request):
    REQUEST_COUNT.inc()
    request_id = str(uuid.uuid4())
    try:
        payload = await request.json()
        logging.info(json.dumps({"request_id": request_id, "payload": payload}))

        if queue.full():
            raise HTTPException(status_code=429, detail="Queue full")

        await queue.put({
            "request_id": request_id,
            "payload": payload,
        })
        QUEUE_DEPTH.set(queue.qsize())

        return {"status": "ok", "request_id": request_id}

    except Exception as e:
        FAILED_COUNT.inc()
        logging.error(json.dumps({"request_id": request_id, "error": str(e)}))
        return {"status": "error", "request_id": request_id, "message": str(e)}

# -------------------
# Health endpoint
# -------------------
@app.get("/health")
async def health():
    return {"status": "healthy"}

# -------------------
# Prometheus metrics
# -------------------
@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

# -------------------
# Kafka batch worker
# -------------------
async def kafka_worker():
    global producer
    while True:
        batch = []
        start_time = asyncio.get_event_loop().time()

        while len(batch) < BATCH_SIZE:
            timeout = BATCH_TIMEOUT - (asyncio.get_event_loop().time() - start_time)
            if timeout <= 0:
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=timeout)
                batch.append(item)
            except asyncio.TimeoutError:
                break

        if batch:
            messages = []
            for item in batch:
                try:
                    msg_bytes = json.dumps(item["payload"]).encode("utf-8")
                    messages.append(msg_bytes)
                except Exception as e:
                    FAILED_BATCH_COUNT.inc()
                    logger.error(f"Serialization error: {e}")

            try:
                # async send to Kafka
                for msg in messages:
                    await producer.send_and_wait(KAFKA_TOPIC, msg)
                BATCH_COUNT.inc()
                logger.info(f"Sent batch of {len(batch)} to Kafka")
            except Exception as e:
                FAILED_BATCH_COUNT.inc()
                logger.error(f"Kafka send error: {e}")

        QUEUE_DEPTH.set(queue.qsize())

# -------------------
# Startup / Shutdown
# -------------------
@app.on_event("startup")
async def startup_event():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await producer.start()
    asyncio.create_task(kafka_worker())
    logger.info("Kafka producer started and worker running")

@app.on_event("shutdown")
async def shutdown_event():
    global producer
    if producer:
        await producer.stop()
    logger.info("Kafka producer stopped gracefully")

# -------------------
# Main
# -------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
