import itertools
import logging
import os
import sys

import psycopg2
from flask import Flask, jsonify, make_response, redirect, request, url_for
from prometheus_flask_exporter import PrometheusMetrics
from psycopg2 import Error

db_name = os.environ.get("DB_NAME")
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASSWORD")
db_host = os.environ.get("DB_HOST")
db_port = os.environ.get("DB_PORT")
db_table = "BLACKLIST"

# test

# db_name = "test_db"
# db_user = "root"
# db_pass = "root"
# db_host = "192.168.1.61"
# db_port = "5432"


def _connect_to_db():
    conn = psycopg2.connect(
        database=db_name, user=db_user, password=db_pass, host=db_host, port=db_port
    )
    return conn


def _create_table():
    try:
        conn = _connect_to_db()
        cursor = conn.cursor()
        sql = f"""CREATE TABLE IF NOT EXISTS {db_table}(
      id serial PRIMARY KEY,
      IP_ADDRESS TEXT,
      DATE TEXT,
      PATH TEXT
    )"""

        cursor.execute(sql)
        conn.commit()
        logging.info("Service table updated successfully")
    except (Exception, Error) as error:
        logging.info("Error while working with PostgreSQL", error)
    finally:
        if conn:
            cursor.close()
            conn.close()
            logging.info("Connection to PostgreSQL closed")


def _insert_data_to_table(ip, date, path):
    try:
        conn = _connect_to_db()
        cursor = conn.cursor()
        sql = f""" INSERT INTO {db_table} (IP_ADDRESS, DATE, PATH)
                                       VALUES ('{ip}','{date}','{path}')"""
        cursor.execute(sql)

        conn.commit()
        count = cursor.rowcount
        logging.info(
            f"{count} The record was successfully added to the {db_table} table"
        )
    except (Exception, Error) as error:
        conn.rollback()
        logging.info("Error while working with PostgreSQL", error)
    finally:
        if conn:
            cursor.close()
            conn.close()
            logging.info("Connection to PostgreSQL closed")


def _return_ip_list():
    try:
        conn = _connect_to_db()
        cursor = conn.cursor()
        sql = f""" SELECT DISTINCT ip_address FROM public.{db_table} """
        cursor.execute(sql)

        conn.commit()
        record = cursor.fetchall()
        logging.info(f"{record} list of blocked ip addresses")
        flatten = list(itertools.chain(*record))
        return flatten
    except (Exception, Error) as error:
        logging.info("Error while working with PostgreSQL", error)
    finally:
        if conn:
            cursor.close()
            conn.close()
            logging.info("Connection to PostgreSQL closed")


def _delete_rows_from_table(ip):
    try:
        conn = _connect_to_db()
        cursor = conn.cursor()
        sql = f""" DELETE FROM {db_table} WHERE ip_address = '{ip}' """
        cursor.execute(sql)

        conn.commit()
        logging.info(f"{ip} unlocked")
    except (Exception, Error) as error:
        logging.info("Error while working with PostgreSQL", error)
    finally:
        if conn:
            cursor.close()
            conn.close()
            logging.info("Connection to PostgreSQL closed")


app = Flask(__name__)
metrics = PrometheusMetrics(app)


@app.route("/")
def index():
    return redirect(url_for("healthz"))


@app.route("/healthz")
def healthz():
    return "OK", 200


@app.route("/addtoblack", methods=["POST"])
def add_to_blacklist():
    input_json = request.get_json(force=True)
    ip = input_json["ip"]
    date = input_json["date"]
    path = input_json["path"]
    _insert_data_to_table(ip, date, path)
    return make_response(jsonify(input_json), 200)


@app.route("/getblack", methods=["POST"])
def get_blacklist():
    block_ip_list = _return_ip_list()
    return make_response(jsonify(block_ip_list), 200)


@app.route("/debug", methods=["POST"])
def debug():
    input_json = request.get_json(force=True)
    return make_response(jsonify(input_json), 200)


@app.route("/unlock", methods=["POST"])
def unlock():
    input_json = request.get_json(force=True)
    ip = input_json["ip"]
    _delete_rows_from_table(ip)
    return make_response(jsonify(f"Unlocked: {ip}"), 200)


if __name__ == "__main__":
    FORMAT = "%(asctime)-15s %(name)s: %(message)s"
    logging.basicConfig(format=FORMAT, stream=sys.stdout, level=logging.INFO)
    _create_table()
    app.run(debug=False, port=8080, host="0.0.0.0")
