import os
import json
import time
from kafka import KafkaConsumer
import psycopg2

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DATABASE_URL = os.getenv("DATABASE_URL")

TOPICS = [
    "ledamoter_topic",
    "voteringar_topic",
    "dokument_topic",
    "kalender_topic",
    "anforanden_topic"
]

BATCH_SIZE = 50


def get_connection():
    while True:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            print("Connected to PostgreSQL")
            return conn
        except Exception as e:
            print("Waiting for DB...", e)
            time.sleep(5)


def create_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ledamoter (
        id TEXT PRIMARY KEY,
        namn TEXT,
        parti TEXT,
        valkrets TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS voteringar (
        id TEXT PRIMARY KEY,
        titel TEXT,
        punkt TEXT,
        riksmote TEXT,
        talare TEXT,
        parti TEXT,
        datum TIMESTAMP,
        rost TEXT,
        intressent_id TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dokument (
        id TEXT PRIMARY KEY,
        titel TEXT,
        datum TEXT,
        typ TEXT,
        organ TEXT,
        parti TEXT,
        dok_url TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kalender (
        id TEXT PRIMARY KEY,
        titel TEXT,
        start TEXT,
        slut TEXT,
        plats TEXT,
        kategori TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS anforanden (
        id TEXT PRIMARY KEY,
        talare TEXT,
        parti TEXT,
        text TEXT,
        intressent_id TEXT
    );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Tables ready")


def insert_message(cur, topic, data):
    if topic == "ledamoter_topic":
        cur.execute(
            "INSERT INTO ledamoter VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (data.get("id"), data.get("namn"), data.get("parti"), data.get("valkrets"))
        )
    elif topic == "voteringar_topic":
        cur.execute(
            "INSERT INTO voteringar VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (data.get("id"), data.get("titel"), data.get("punkt"),
             data.get("riksmote"), data.get("talare"), data.get("parti"),
             data.get("datum"), data.get("rost"), data.get("intressent_id"))
        )
    elif topic == "dokument_topic":
        cur.execute(
            "INSERT INTO dokument VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (data.get("id"), data.get("titel"), data.get("datum"),
             data.get("typ"), data.get("organ"), data.get("parti"), data.get("dok_url"))
        )
    elif topic == "kalender_topic":
        cur.execute(
            "INSERT INTO kalender VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (data.get("id"), data.get("titel"), data.get("start"),
             data.get("slut"), data.get("plats"), data.get("kategori"))
        )
    elif topic == "anforanden_topic":
        cur.execute(
            "INSERT INTO anforanden VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (data.get("id"), data.get("talare"), data.get("parti"),
             data.get("text"), data.get("intressent_id"))
        )


def run_consumer():
    create_tables()
    conn = get_connection()
    cur = conn.cursor()

    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_SERVER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id="riksdagen-group",
        enable_auto_commit=False
    )

    print("Kafka consumer started")
    count = 0

    for message in consumer:
        topic = message.topic
        data = message.value

        try:
            insert_message(cur, topic, data)
            count += 1
            print(f"{topic} -> {data.get('id')}")

            if count >= BATCH_SIZE:
                conn.commit()
                consumer.commit()
                print(f"Committed {count} rows")
                count = 0

        except Exception as e:
            print(f"Insert error på {topic}: {e}")
            conn.rollback()
            cur.close()
            cur = conn.cursor()

    if count > 0:
        conn.commit()
        consumer.commit()
        print(f"Final commit {count} rows")


def main():
    while True:
        try:
            run_consumer()
        except Exception as e:
            print("Consumer crashed:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()