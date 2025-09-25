#
# This script should only be run WITHIN the container.
#

if ! sudo /opt/splunk/bin/splunk list index -auth admin:Password1234 | grep -q digit_sysdiagnose; then
    echo "Setting up Splunk index for the first time"
    # create the index
    sudo /opt/splunk/bin/splunk add index digit_sysdiagnose -auth admin:Password1234

    echo "Installing the EC-DIGIT-TA"
    # download and extract the TA
    wget https://github.com/EC-DIGIT-CSIRC/ec_digit_saf_ta/archive/refs/heads/main.tar.gz -O /tmp/ec_digit_saf_ta.tar.gz

    sudo mkdir -p /opt/splunk/etc/apps/ec_digit_saf_ta
    sudo tar -C /opt/splunk/etc/apps/ec_digit_saf_ta --strip-components=1 -xzf /tmp/ec_digit_saf_ta.tar.gz

    # create the local version of the files
    sudo mkdir -p /opt/splunk/etc/apps/ec_digit_saf_ta/local
    sudo chmod 777 /opt/splunk/etc/apps/ec_digit_saf_ta/local

    cat <<EOT > /opt/splunk/etc/apps/ec_digit_saf_ta/local/inputs.conf
[monitor:///cases/*/parsed_data/*.jsonl]
disabled = false
index = digit_sysdiagnose
sourcetype = digit:saf:parseddata:json
host_segment = 2

[monitor:///cases/*/logs/*.jsonl]
disabled = false
index = digit_sysdiagnose
sourcetype = digit:saf:logs:json
host_segment = 2
# Rotating logs
crcSalt = <SOURCE>

[script://$SPLUNK_HOME/etc/apps/ec_digit_saf_ta/bin/read_cases.py]
disabled = false
index = digit_sysdiagnose
sourcetype = digit:saf:cases:json
python.version = python3
interval = 300
EOT

    cat <<EOT > /opt/splunk/etc/apps/ec_digit_saf_ta/local/ec_digit_saf_ta_settings.conf
[cases]
# folder = /opt/sysdiagnose/cases
folder = /cases

[logging]
# loging level: INFO
# https://docs.python.org/3/library/logging.html#logging-levels
# Possible values: DEBUG (10), INFO (20), WARNING (30), ERROR (40), CRITICAL (50)
level = 20
max_size_mb = 1
max_backup_files = 2
EOT

    sudo -u splunk /opt/splunk/bin/splunk restart
fi

echo "Finished installing Technical Addon. You can access the Splunk web interface at http://localhost:8000 (username: admin, password: Password1234)"

