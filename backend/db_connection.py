# backend/db_connection.py
from cassandra.cluster import Cluster
from cassandra.io.asyncioreactor import AsyncioConnection    # ✅ use asyncio instead

KEYSPACE = "iot_data"

def get_cluster_session():
    cluster = Cluster(
        contact_points=["127.0.0.1"],
        port=9042,
        connection_class=AsyncioConnection   # ✅ use asyncio instead of asyncore
    )
    session = cluster.connect()
    return cluster, session

def init_db(session):
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': '1' }}
    """)
    session.set_keyspace(KEYSPACE)

    session.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            sensor_id text,
            ts timestamp,
            pm2_5 double,
            pm10 double,
            temperature double,
            humidity double,
            PRIMARY KEY (sensor_id, ts)
        ) WITH CLUSTERING ORDER BY (ts DESC);
    """)
