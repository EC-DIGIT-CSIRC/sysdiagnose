
# Workshop docker compose

This docker-compose was made for the workshop organised at conferences.

To start:
```
docker-compose up -d
```
The first time, and once you can load the webpage:
```
sudo docker compose exec splunk /bin/bash /add-ta.sh
```

To stop without data deletion
```
docker-compose stop
```

To start from existing instance
```
docker-compose start
```

To stop and remove data:
```
docker-compose down
```

To list data
```
docker-compose images
```

To delete:
```
docker-compose rm splunk
```
