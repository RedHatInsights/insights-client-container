#!/bin/bash

docker build . -t quay.io/jjaggars/insights-client-container
docker push quay.io/jjaggars/insights-client-container
