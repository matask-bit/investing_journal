# db.py
import psycopg2
import os

DB_URL = "postgresql://tracker_user:tracker_pass@localhost:5432/trading_tracker"

def get_connection():
    return psycopg2.connect(DB_URL)

