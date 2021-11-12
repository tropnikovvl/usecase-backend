# usecase-backend

**IMPORTANT**: This product may only be used for test purposes. Not for the production environment

## About This Repository

This repository contains a test version of the web application.
It accepts API queries and based on them blocks or unblocks the user and sends an email about the event.

**Flask_routes:**
- "/" - redirects to healtz
- "/healthz" - http check application status
- "/addtoblack" - receives IP, DATE, URL_PATH parameters in json form, creates entries about it in the database and sends an email with the blocked address
- "/getblack" - returns the list of IP addresses from the database
- "/unlock" - receives the IP, deletes it from the database, sends an email about the event
- "/debug" - returns json with parameters: IP, DATA, URL_PATH.
- "/metrics" - flask metrics in prometheus format

## Pre-requisites

Your computer must have the following settings installed and configured:
- python3
- pip3

## How to install automatically
- bash install.sh

## How to install Manually

**deploy Kubernetes:**
- helm upgrade -i -n dev -f helm/usecase-backend/values.yaml backend helm/usecase-backend

**deploy Docker (example):**
- docker run --rm -d --name backend \
-e DB_USER="root" \
-e DB_PASSWORD="root" \
-e DB_NAME="test_db" \
-e DB_HOST="192.168.1.61" \
-e DB_PORT="5432" \
-e MAIL_SERVER="smtp.yandex.ru" \
-e MAIL_PORT="587" \
-e MAIL_RECIPIENT="your_mail_recipient" \
-e MAIL_USE_TLS="True" \
-e MAIL_USE_SSL="False" \
-e MAIL_USERNAME="your_main_account" \
-e MAIL_PASSWORD="your_main_password" \
-p 8080:8080 \
tropnikovvl/usecase-backend:latest
