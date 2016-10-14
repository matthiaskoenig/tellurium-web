#!/usr/bin/env bash
docker build --no-cache -t matthiaskoenig/teweb . && docker run -it -p 8000:8000 matthiaskoenig/teweb