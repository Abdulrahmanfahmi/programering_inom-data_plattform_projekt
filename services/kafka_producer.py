from kafka import KafkaProducer
import json
import os


KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def send_to_kafka(topic, data):

    for row in data:
        producer.send(topic, row)

    producer.flush()

    print(f"Skickade {len(data)} meddelanden till topic: {topic}")