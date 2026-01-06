# Timesketch


Installation instructions of timesketch : https://timesketch.org/guides/admin/install/


# SAF specifics
## To start timesketch:
```bash
cd timesketch
sudo docker compose up -d
```

## To stop timesketch:
```
sudo docker compose down
```


## To import SAF data

- Once Timesketch runs we need to ingest our data.

- within your venv you need to install the requirements.txt
`pip install timesketch-import-client`

To import SAF data once.


To import SAF data continuously


