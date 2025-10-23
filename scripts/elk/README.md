# Hardware requirements

From a quick and dirty test, you should set up at least: 8 CPUs, 32 GB RAM, 120 GB disk for the docker VM.

Example: using Colima

```bash
# stop current Colima VM
colima stop

# start Colima with more resources (example: 8 CPUs, 32 GB RAM, 120 GB disk)
colima start --cpu 8 --memory 32 --disk 120

# verify Colima is running
colima status

# Create the containers
docker compose up -d
```

# References

- <https://discuss.elastic.co/t/no-logs-from-logstash-docker/342882/6>
