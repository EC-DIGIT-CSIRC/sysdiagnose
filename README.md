# Sysdiagnose analysis framework

![sysdiagnose-512x512](https://github.com/EC-DIGIT-CSIRC/sysdiagnose/assets/750019/2742ca75-758e-4393-a2d1-5c94d09b0eb3)

# Installation

Note that you will need Python 3.11 or higher.

Create a virtual environment and install dependencies:

```bash
 python3 -m venv venv
 source venv/bin/activate
 pip install .
 sudo apt install graphviz
 ```

On linux systems you may wish to install the [unifiedlogs](#unifiedlogs) parser. See below for instructions how to do this.

# Quickstart

## Case management

Creating a new case, with the optional `-c` parameter if you want to specify the case number yourself. (such as an uuid)

```bash
$ sysdiag init test-data/iOS12/sysdiagnose_2019.02.13_15-50-14+0100_iPhone_OS_iPhone_16C101.tar.gz

Sysdiagnose file has been processed
Case ID: 1
```

Listing existing cases can be done easily:

```bash
$ sysdiag cases
Case ID              acquisition date           Serial number    Unique device ID                          iOS Version    Tags
-------------------  -------------------------  ---------------  ----------------------------------------  -------------  ------
public               2023-05-24T13:29:15-07:00  F4GT2K24HG7K     e22f7f830e5dcc1287a1690a2622c2b12afaa33c  <unknown>
```

The `cases` folder is the current folder by default.
You can change this using the environment variable `SYSDIAGNOSE_CASES_PATH`, for example.

```bash
$ export SYSDIAGNOSE_CASES_PATH='/path/to/folder'
$ sysdiag list cases
```

## Parsing data and converting it to a usable format

Data of sysdiagnose is not always usable directly, use parsers to convert them to a nice json file.

Run parsers:

```bash
$ sysdiag -c 1 parse ps
Execution success, output saved in: cases/1/parsed_data/ps.json

$ sysdiag -c 1 parse sys
Execution success, output saved in: cases/1/parsed_data/sys.json
```

To run on all cases do not specify a case number or use `-c all`.

List available parsers :

```bash
$ sysdiag list parsers
Parser Name            Parser Description
---------------------  ---------------------------------------------------------------------
all                    Run all parsers
accessibility_tcc      Parsing Accessibility TCC logs
appinstallation        Parsing app installation logs
brctl                  Parsing brctl files
containermanager       Parsing containermanagerd logs file
crashlogs              Parsing crashes folder
demo_parser            Demo parsers
itunesstore            Parsing iTunes store logs
lockdownd              Parsing lockdownd logs file
logarchive             Parsing system_logs.logarchive folder
mobileactivation       Parsing mobileactivation logs file
mobileinstallation     Parsing mobile_installation logs file
networkextension       Parsing networkextension plist file
networkextensioncache  Parsing networkextensioncache plist file
olddsc                 Parsing olddsc files
plists                 Parsing any pslist into json
powerlogs              Parsing powerlogs database
ps                     Parsing ps.txt file
psthread               Parsing ps_thread.txt file
remotectl_dumpstate    Parsing remotectl_dumpstate file containing system information
security_sysdiagnose   Parsing security-sysdiagnose.txt file containing keychain information
shutdownlogs           Parsing shutdown.log file
spindumpnosymbols      Parsing spindump-nosymbols file
swcutil                Parsing swcutil_show file
sys                    Parsing SystemVersion plist file
taskinfo               Parsing taskinfo txt file
uuid2path              Parsing UUIDToBinaryLocations plist file
wifi_known_networks    Parsing Known Wifi Networks plist file
wifinetworks           Parsing com.apple.wifi plist files
wifiscan               Parsing wifi_scan files
wifisecurity           Parsing WiFi Security logs
```

## Analysers to process parsed data

List analysers:

```bash
$ sysdiag list analysers
Analyser Name         Analyser Description
--------------------  -------------------------------------------------------------------------------
all                   Run all analysers
apps                  Get list of Apps installed on the device
demo_analyser         Do something useful (DEMO)
ps_everywhere         List all processes we can find a bit everywhere.
ps_matrix             Makes a matrix comparing ps, psthread, taskinfo
timesketch            Generate a Timesketch compatible timeline
wifi_geolocation      Generate GPS Exchange (GPX) of wifi geolocations
wifi_geolocation_kml  Generate KML file for wifi geolocations
yarascan              Scan the case folder using YARA rules ('./yara' or SYSDIAGNOSE_YARA_RULES_PATH)
```

Run analyser (make sure you run `parse all` before)

```bash
$ sysdiag -c 1 analyse timesketch
Execution success, output saved in: cases/1/parsed_data/timesketch.jsonl
```

# Using the output

Most of the parsers and analysers save their results in `jsonl` or `json` format. A few analysers use `txt` and more.
Exported data is stored in the `<cases>/<case_id>/parsed_data` folder. You can configure your ingestion tool to automatically monitor and all that data.

The JSONL files are event based and (most often) structured with a a `timestamp` (unixtime) and `datetime` (isoformat) field. These can be used to build timelines.

## Timesketch

You might want to visualise timelines which you can extract via sysdiagnose in [Timesketch](https://timesketch.org/guides/admin/install/). Do note that timesketch expects timestamps in microseconds, that's why we made the `timesketch` analyser.

Note that for a reasonable sysdiagnose log output, we recommend the following base requirements:

- Ubuntu 20.04 or higher
- 128GB of RAM
- 4-8 virtual CPUs
- Minimum 64 GB of HDD space just for timesketch data (add some more GBs for the OS and OS upgrades, etc.)
- SSDs (NVMEs) for the data.

## Yarascan

Using YARA rules are an easy and flexible way of spotting 'evil', the Yarascan analyser will help you out with that. It looks for YARA rules within __.yar__ files saved in the `./yara` folder or in the one designated by the environment varirable `SYSDIAGNOSE_YARA_RULES_PATH`.

# UnifiedLogs

This unifiedlogs parser tool is natively provided on a MacOS system. Fortunately some entities developed a linux compatible parser.

By default sysdiagnose will use the Apple unifiedlogs `log` binary.
On linux it expects the Mandiant developed UnifiedLogs tool to be present in the path. Follow below instructions to compile and install it on your system.

## Building macos-UnifiedLogs for linux

First, ensure `cargo` is installed so you can build rust projects.

```bash
sudo apt install cargo
```

Now you can download and compile the code:

```bash
git clone https://github.com/mandiant/macos-UnifiedLogs
cd macos-UnifiedLogs/examples/unifiedlog_iterator/
cargo build --release
sudo cp ../target/release/unifiedlog_iterator /usr/local/bin/
```

See `unifiedlog_iterator --help` for more instructions to use the tool, or use it directly through sysdiagnose.

# Troubleshooting

By default, whenever you [parse](#parsing-data-and-converting-it-to-a-usable-format) or [analyse](#analysers-to-process-parsed-data) data, the framework generates a log file in JSONL format in the subfolder `logs` located in the case folder.

__Note:__ You can get that very same information in the output by adding the flag `-l DEBUG` to the parse/analyse command. But this is not very manageable when using all parsers/analysers.

You will be able to identify the execution of a parser/analyser by, at least, two entries generated by the main module (__module: main__) with an extra field named parser/analyser that contains the name of the parser/analyser.

In between those two entries, you may see any other produced by the parser/analyser, where the module, this time, will match the parser/analyser name.

__Note:__ It is of utmost important that the parser/analyser provides logging to help troubleshooting potential issues. Please take a look to the [demo_parser](src/sysdiagnose/parsers/demo_parser.py) and the [demo_analyser](src/sysdiagnose/analysers/demo_analyser.py) files for inspiration.

Below you can find an example of traces within the log file.

```json
{"levelname": "INFO", "module": "main", "message": "Parser 'demo_parser' started", "taskName": null, "parser": "demo_parser", "datetime": "2025-01-28T12:16:59.153931+01:00", "timestamp": 1738063019.153931}
{"levelname": "INFO", "module": "demo_parser", "message": "Processing file ./cases/1/data/sysdiagnose_2024.09.18_11-33-57+0200_iPhone-OS_iPhone_21G93/demo_input_file.txt, new entry added", "taskName": null, "log_file": "./cases/1/data/sysdiagnose_2024.09.18_11-33-57+0200_iPhone-OS_iPhone_21G93/demo_input_file.txt", "entry": "{}", "datetime": "2025-01-28T12:16:59.201914+01:00", "timestamp": 1738063019.201914}
{"levelname": "WARNING", "module": "demo_parser", "message": "Empty entry.", "taskName": null, "datetime": "2025-01-28T12:16:59.202071+01:00", "timestamp": 1738063019.202071}
{"levelname": "INFO", "module": "main", "message": "Parser 'demo_parser' finished successfully", "taskName": null, "parser": "demo_parser", "result": 0, "datetime": "2025-01-28T12:16:59.202495+01:00", "timestamp": 1738063019.2024949}

```

# Supported iOS versions

Tested on:

- python 3.11
- iOS13 (to be confirmed)
- iOS14 (to be confirmed)
- iOS15
- iOS16
- iOS17
- iOS18

# Contributors

- Dario BORREGUERO RINCON (European Commission - EC DIGIT Cybersecurity Operation Centre)
- David DURVAUX (European Commission - EC DIGIT Cybersecurity Operation Centre)
- Aaron KAPLAN (European  Commission - EC DIGIT Cybersecurity Operation Centre)
- Christophe VANDEPLAS (European Commission - EC DIGIT Cybersecurity Operation Centre)
- Emilien  LE JAMTEL (CERT-EU)
- Benoît ROUSSILLE (European Parliament)
- For the Apollo library: https://github.com/mac4n6/APOLLO

# Licence

This project is released under the European Public Licence
https://commission.europa.eu/content/european-union-public-licence_en
