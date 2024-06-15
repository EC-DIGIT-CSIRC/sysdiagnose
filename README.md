# Sysdiagnose analysis framework

![sysdiagnose-512x512](https://github.com/EC-DIGIT-CSIRC/sysdiagnose/assets/750019/2742ca75-758e-4393-a2d1-5c94d09b0eb3)


# Installation

Note that you will need Python 3.6 or higher.

Create a virtual environment:

```bash
 virtualenv --python python3.10 venv
 source venv/bin/activate
 ```

 Install dependencies:
 ```bash
 pip install -r requirements.txt
 sudo apt install graphviz
 ```

On linux systems you may wish to install the unifiedlogs parser. See below for instructions how to do this.


# Quickstart

Add new sysdiagnose case:

```
$ python initialise.py file test-data/iOS12/sysdiagnose_2019.02.13_15-50-14+0100_iPhone_OS_iPhone_16C101.tar.gz
d280f515593b3570a781890296b2a394b3dffc298212af0d195765a7cf1cd777
Sysdiagnose file has been processed
New case ID: 1
```

List available parsers and cases:

```
$ python parsing.py list parsers
Parser Name            Parser Description                        Parser Input
---------------------  ----------------------------------------  ---------------------
demo_parser            Demo parsers                              demo_input_file
logarchive             Parsing system_logs.logarchive folder     logarchive_folder
ps                     Parsing ps.txt file                       ps
spindumpnosymbols      Parsing spindump-nosymbols file           spindump-nosymbols
accessibility_tcc      Parsing Accessibility TCC logs            Accessibility-TCC
taskinfo               Parsing taskinfo txt file                 taskinfo
networkextensioncache  Parsing networkextensioncache plist file  networkextensioncache
mobileactivation       Parsing mobileactivation logs file        mobile_activation
networkextension       Parsing networkextension plist file       networkextension
wifisecurity           Parsing WiFi Security logs                wifisecurity
swcutil                Parsing swcutil_show file                 swcutil_show
sys                    Parsing SystemVersion plist file          systemversion
appinstallation        Parsing app installation logs             appinstallation
powerlogs              Parsing  powerlogs database               powerlogs
olddsc                 Parsing olddsc files                      olddsc
mobileinstallation     Parsing mobile_installation logs file     mobile_installation
itunesstore            Parsing iTunes store logs                 itunesstore
containermanager       Parsing containermanagerd logs file       container_manager
wifi_known_networks    Parsing Known Wifi Networks plist file    wifi_data
psthread               Parsing ps_thread.txt file                ps_thread
wifiscan               Parsing wifi_scan files                   wifi_data
shutdownlogs           Parsing shutdown.log file                 shutdownlog
uuid2path              Parsing UUIDToBinaryLocations plist file  UUIDToBinaryLocations
brctl                  Parsing brctl files                       brctl

$ python parsing.py list cases
#### case List ####
  Case ID  Source file                                                                          SHA256
---------  -----------------------------------------------------------------------------------  ----------------------------------------------------------------
        1  test-data/iOS12/sysdiagnose_2019.02.13_15-50-14+0100_iPhone_OS_iPhone_16C101.tar.gz  d280f515593b3570a781890296b2a394b3dffc298212af0d195765a7cf1cd777
```

Run parsers:

```
$ python parsing.py parse ps 1
Execution success, output saved in: ./parsed_data/1/ps.json

$ python parsing.py parse sys 1
Execution success, output saved in: ./parsed_data/1/sys.json
```

List analysers:

```
$ python analyse.py list analysers
nalyser Name         Analyser Description
--------------------  ------------------------------------------------
apps                  Get list of Apps installed on the device
wifi_geolocation_kml  Generate KML file for wifi geolocations
timeliner             Generate a Timesketch compatible timeline
wifi_geolocation      Generate GPS Exchange (GPX) of wifi geolocations
demo_analyser         Do something useful (DEMO)
```

Run analyser (make sure you run `allparsers` before)
```
$ python analyse.py analyse timeliner 1
Execution success, output saved in: ./parsed_data/1/timeliner.jsonl
```

Tested On:
- python 3.11
- iOS13 (to be confirmed)
- iOS14 (to be confirmed)
- iOS15
- iOS16
- iOS17


# Timesketch

You might want to visualise timelines which you can extract via sysdiagnose in [Timesketch](https://timesketch.org/guides/admin/install/).
Note that for a reasonable sysdiagnose log output, we recommend the following base requirements:

- Ubuntu 20.04 or higher
- 128GB of RAM
- 4-8 virtual CPUs
- Minimum 64 GB of HDD space just for timesketch data (add some more GBs for the OS and OS upgrades, etc.)
- SSDs (NVMEs) for the data.

# UnifiedLogs
This unifiedlogs parser tool is natively provided on a MacOS system. Fortunately some entities developed a linux compatible parser.

By default sysdiagnose will use the Apple unifiedlogs `log` binary.
On linux it expects the Mandiant developed UnifiedLogs tool to be present in the path. Follow below instructions to compile and install it on your system.

## Building macos-UnifiedLogs for linux

First, ensure `cargo` is installed so you can build rust projects.
```
sudo apt install cargo
```
Now you can download and compile the code:
```bash
git clone https://github.com/mandiant/macos-UnifiedLogs
cd macos-UnifiedLogs/examples/unifiedlog_parser_json/
cargo build --release
sudo cp ../target/release/unifiedlog_parser_json /usr/local/bin/
```
See `unifiedlog_parser_json --help` for more instructions to use the tool, or use it directly through sysdiagnose.

# Contributors

- Dario BORREGUERO RINCON (European Commission - EC DIGIT Cybersecurity Operation Centre)
- David DURVAUX (European Commission - EC DIGIT Cybersecurity Operation Centre)
- Aaron KAPLAN (European  Commission - EC DIGIT Cybersecurity Operation Centre)
- Christophe VANDEPLAS (European Commission - EC DIGIT Cybersecurity Operation Centre)
- Emilien  LE JAMTEL (CERT-EU)
- Benoît ROUSSILLE (European Parliament)


# License
This project is released under the European Public Licence
https://commission.europa.eu/content/european-union-public-licence_en



