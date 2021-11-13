import itertools
import logging
import os
import sys

import psycopg2
from flask import Flask, jsonify, make_response, redirect, request, url_for
from flask_mail import Mail, Message
from prometheus_flask_exporter import PrometheusMetrics
from psycopg2 import Error

db_name = os.environ.get("DB_NAME").rstrip()
db_user = os.environ.get("DB_USER").rstrip()
db_pass = os.environ.get("DB_PASSWORD").rstrip()
db_host = os.environ.get("DB_HOST").rstrip()
db_port = os.environ.get("DB_PORT").rstrip()
db_table = "BLACKLIST"

mail_server = os.environ.get("MAIL_SERVER").rstrip()
mail_port = int(os.environ.get("MAIL_PORT").rstrip())
mail_username = os.environ.get("MAIL_USERNAME").rstrip()
mail_password = os.environ.get("MAIL_PASSWORD").rstrip()
mail_recipient = os.environ.get("MAIL_RECIPIENT").rstrip()
mail_use_tls = eval(os.environ.get("MAIL_USE_TLS").rstrip())
mail_use_ssl = eval(os.environ.get("MAIL_USE_SSL").rstrip())


def _connect_to_db():
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_pass,
        host=db_host,
        port=db_port,
        connect_timeout=3,
        keepalives=1,
        keepalives_idle=5,
        keepalives_interval=2,
        keepalives_count=2,
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
            logging.info("Initial connection to PostgreSQL closed")


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


def _send_email(subject, body):
    try:
        msg = Message(
            subject=subject,
            recipients=[mail_recipient],
            body=body,
            sender=mail_username,
        )
        with app.app_context():
            mail.send(msg)
        logging.info("Email has been send")
    except (Exception, Error) as error:
        logging.info("Error while working with Mail", error)
    return "OK"


app = Flask(__name__)
metrics = PrometheusMetrics(app)

app.config["MAIL_SERVER"] = mail_server
app.config["MAIL_PORT"] = mail_port
app.config["MAIL_USERNAME"] = mail_username
app.config["MAIL_PASSWORD"] = mail_password
app.config["MAIL_USE_TLS"] = mail_use_tls
app.config["MAIL_USE_SSL"] = mail_use_ssl

mail = Mail(app)


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
    body = f"Ip {ip} has been blocked"
    date = input_json["date"]
    path = input_json["path"]
    _insert_data_to_table(ip, date, path)
    subject = "Block IP"
    _send_email(subject, body)
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
    body = f"Ip {ip} has been unblocked"
    _delete_rows_from_table(ip)
    subject = "Unblock IP"
    _send_email(subject, body)
    return make_response(jsonify(f"Unlocked: {ip}"), 200)


if __name__ == "__main__":
    FORMAT = "%(asctime)-15s %(name)s: %(message)s"
    logging.basicConfig(format=FORMAT, stream=sys.stdout, level=logging.INFO)
    _create_table()
    app.run(debug=False, port=8080, host="0.0.0.0")
