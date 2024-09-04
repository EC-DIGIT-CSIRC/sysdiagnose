# List of usefull commands

List all the files in an extracted archive and obtain types:
```
find . -type f -exec file {} \;  > ../iOS13-all-files.txt
````

Convert automatically binary plist to JSON:
````
find .  -type f -name "*.plist" -exec sh -c 'plutil -convert json -r $1' - {} \;
````

For the PLIST that could not be converted (due to serialized object), drop a human version with .txt extension:
````
find .  -type f -name "*.plist" -exec sh -c 'plutil -p $1 > $1.txt'  - {} \;
````

# Backup the device with libimobile device

To install
````
apt-get install libimobiledevice-dev libimobiledevice-doc libimobiledevice6 libplist-doc ideviceinstaller libimobiledevice-utils python-imobiledevice python-plist libplist-utils
````

List connected devices:
````
david@porg:~/git$ idevice_id  -l
57903aef990b53f80bc712efae0e6cb320e28c3a
````

Pair the device:
````
david@porg:~/git$ idevicepair pair -u 57903aef990b53f80bc712efae0e6cb320e28c3a
SUCCESS: Paired with device 57903aef990b53f80bc712efae0e6cb320e28c3a
````

Trigger a backup
````
david@porg:~/git$ idevicebackup2 -u 57903aef990b53f80bc712efae0e6cb320e28c3a backup ~/Documents/iPhoneBackups/
Backup directory is "~/Documents/iPhoneBackups/"
Started "com.apple.mobilebackup2" service on port 49734.
Negotiated Protocol Version 2.1
Starting backup...
Backup will be unencrypted.
Requesting backup from device...
Full backup mode.
[==========================                        ]  50% Finished
Receiving files
[==================================================] 100% (5.2 MB/5.2 MB)
[==================================================] 100% (5.2 MB/5.2 MB)
[...]
Sending '57903aef990b53f80bc712efae0e6cb320e28c3a/Status.plist' (189 Bytes)
Sending '57903aef990b53f80bc712efae0e6cb320e28c3a/Manifest.plist' (63.7 KB)
````

Unpack the backup
````
idevicebackup2 unback ~/Documents/iPhoneBackups/
````


# SQLite DB on iOS13

At first glance, only 2 remains:
````
$find .  -type f -name "*.sqlitedb"
./logs/itunesstored/downloads.28.sqlitedb
./logs/appinstallation/appstored.sqlitedb

# Parsing unified logging:
https://github.com/ydkhatri/UnifiedLogReader

# Count rows in powerlogs
db="filename"
for i in `sqlite3 "$db" "SELECT name FROM sqlite_master WHERE type='table';"`; do  a=$(sqlite3 "$db" "SELECT COUNT(*) FROM '$i'"); echo -e "$a\t$i"; done | sort -n  > powerlogs_cnt

