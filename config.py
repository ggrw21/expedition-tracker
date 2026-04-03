import mysql.connector
import time
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_ssl_ca_path():
    configured_path = os.getenv("MYSQL_SSL_CA")
    if configured_path:
        return configured_path

    repo_cert = BASE_DIR / "Hardware scripts" / "ca.pem"
    if repo_cert.exists():
        return str(repo_cert)

    if os.name == 'posix':
        return '/home/daybroken/Desktop/NEA/ca.pem'
    if os.name == 'nt':
        return r"G:\Other computers\Mac\Year12\CS\NEA\Iterations\Resources\ca.pem"
    return None

def DBconnect():
    while True:
        try:
            ssl_ca = _get_ssl_ca_path()

            # Connect to the MySQL database and specify the database
            mydb = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "tracker-db-nea-tracker.h.aivencloud.com"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                port=int(os.getenv("MYSQL_PORT", "21950")),
                database=os.getenv("MYSQL_DATABASE", "defaultdb"),
                ssl_ca=ssl_ca
            )
            print("Connected to MySQL!")
            return mydb
        except mysql.connector.Error as e:
            print("Error Connecting, retrying...")
            print(f"Error: {e}")
            time.sleep(3)
