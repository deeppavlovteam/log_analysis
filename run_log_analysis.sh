#!/bin/bash
source ./env/bin/activate && \
nohup jupyter lab --no-browser > ./log_analysis.log 2>&1 &