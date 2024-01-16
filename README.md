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

# Quickstart

Add new sysdiagnose case

```
$ python initialyze.py file test-data/iOS12/sysdiagnose_2019.02.13_15-50-14+0100_iPhone_OS_iPhone_16C101.tar.gz 
d280f515593b3570a781890296b2a394b3dffc298212af0d195765a7cf1cd777
Sysdiagnose file has been processed
New case ID: 1

```

List available parsers and cases

```
$ python parsing.py list parsers
Parser Name      Parser Description                Parser Input
---------------  --------------------------------  --------------
sysdiagnose-ps   Parsing ps.txt file               ps
sysdiagnose-sys  Parsing SystemVersion plist file  systemversion

$ python parsing.py list cases
#### case List ####
  Case ID  Source file                                                                          SHA256
---------  -----------------------------------------------------------------------------------  ----------------------------------------------------------------
        1  test-data/iOS12/sysdiagnose_2019.02.13_15-50-14+0100_iPhone_OS_iPhone_16C101.tar.gz  d280f515593b3570a781890296b2a394b3dffc298212af0d195765a7cf1cd777
```

Run parsers

```
$ python parsing.py parse sysdiagnose-ps 1
Execution success, output saved in: ./parsed_data/1/sysdiagnose-ps.json

$ python parsing.py parse sysdiagnose-sys 1
Execution success, output saved in: ./parsed_data/1/sysdiagnose-sys.json

```

Tested On:
- python 3.8.5, 3.10
- iOS13
- iOS14
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

# Contributors

- Dario BORREGUERO RINCON (European Commission - EC DIGIT Cybersecurity Operation Centre)
- David DURVAUX (European Commission - EC DIGIT Cybersecurity Operation Centre)
- Aaron KAPLAN (European  Commission - EC DIGIT Cybersecurity Operation Centre)
- Emilien  LE JAMTEL (CERT-EU)
- Benoît ROUSSILLE (European Parliament)


# License
This project is released under the European Public Licence
https://commission.europa.eu/content/european-union-public-licence_en



