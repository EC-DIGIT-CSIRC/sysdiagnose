# sysdiagnose-timeline
Sysdiagnose timeliner

# Quick and ugly howto

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
- iOS13
- iOS14
- iOS16 (ongoing)


# Requirements

Python package:
```
pip3 install graphviz
```

Binaries
```
graphiz (dot)

```



