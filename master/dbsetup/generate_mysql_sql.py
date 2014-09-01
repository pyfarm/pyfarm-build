from os.path import join, dirname, abspath

import yaml


CONFIG = join(dirname(abspath(__file__)), "config.yml")

with open(CONFIG, "r") as config:
    config = yaml.load(config)


for database in config["databases"]:
    print "DROP DATABASE IF EXISTS %s;" % database

print "GRANT USAGE ON *.* TO '%s'@'%%';" % config["username"]
print "DROP USER '%s'@'%%';" % config["username"]
print "CREATE USER '%s'@'%%' IDENTIFIED BY '%s';" % (config["username"], config["password"])

for database in config["databases"]:
    print "CREATE DATABASE %s;" % database

for database in config["databases"]:
    print "GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%%' IDENTIFIED BY '%s';" % (
        database, config["username"], config["password"])