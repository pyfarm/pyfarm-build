from os.path import join, dirname, abspath

import yaml


CONFIG = join(dirname(abspath(__file__)), "config.yml")

with open(CONFIG, "r") as config:
    config = yaml.load(config)


for database in config["databases"]:
    print "DROP DATABASE IF EXISTS %s;" % database

print "DROP ROLE IF EXISTS %s;" % config["username"]
print "CREATE ROLE %s WITH ENCRYPTED PASSWORD '%s';" % (config["username"], config["password"])

for database in config["databases"]:
    print "CREATE DATABASE %s OWNER %s;" % (database, config["username"])
