"connections to storage"

import psycopg2.pool, redis, os

PG_POOL = None
REDIS = None

def connect_all():
  connect_pg()
  connect_redis()

def connect_pg():
  global PG_POOL
  PG_POOL = psycopg2.pool.ThreadedConnectionPool(0, 4, os.environ['AUTOMIG_CON'])

def connect_redis():
  global REDIS
  REDIS = redis.Redis(os.environ['REDIS_HOST'])
