#!/bin/bash

helm upgrade -i -n dev -f helm/usecase-backend/values.yaml backend helm/usecase-backend
