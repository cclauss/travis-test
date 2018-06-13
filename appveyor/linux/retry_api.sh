#!/bin/bash

sleep 10

for i in $(seq 1 3); do
  curl -v http://localhost:8000/api/v2/reflection/api-methods --user admin:e2e_tests
  sleep 1
done;
