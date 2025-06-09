#!/bin/bash

gunicorn app.src.main:app -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:80 --timeout 1000