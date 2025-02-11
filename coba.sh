#!/bin/bash

CONFIG_FILE="config.cfg"

DB_HOST=$(python3 -c "import configparser; config = configparser.ConfigParser(); config.read('$CONFIG_FILE'); print(config['server']['host'])")
DB_PORT=$(python3 -c "import configparser; config = configparser.ConfigParser(); config.read('$CONFIG_FILE'); print(config['server']['port'])")

echo "Database host: $DB_HOST"
echo "Database port: $DB_PORT"