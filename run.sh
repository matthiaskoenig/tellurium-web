#!/usr/bin/env bash
docker build -t matthiaskoenig/teweb . && docker run -it -p 8000:8000 matthiaskoenig/teweb