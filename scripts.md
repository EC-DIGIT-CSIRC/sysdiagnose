# List of scripts developped

| Script | Default output (CLI) | Method JSON |
| ------ | -------------------- | ----------- |
| sysdiagnose-ps.py | Print the process as a tree from ps.txt |  parse_ps(filename) <br/> export_to_json(processes, filename="./ps.json") |
| sysdiagnose-sys.py | Print the information on the iOS device used | getProductInfo(path) |
