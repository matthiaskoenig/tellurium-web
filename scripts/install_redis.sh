#!/usr/bin/env bash
############################################################
# Redis setup
#
# Redis, developed in 2009, is a flexible, open-source, key value data store.
# Following in the footsteps of other NoSQL databases, such as Cassandra, CouchDB, and MongoDB,
# Redis allows the user to store vast amounts of data without the limits of a relational database.
#
# see: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-redis
#
# Usage:
# 	./install_redis.sh 2>&1 | tee ./install_redis.log
############################################################

date
echo "--------------------------------------"
echo "redis installation"
echo "--------------------------------------"

# message broker and celery
sudo apt-get install -y build-essential tcl
sudo apt-get install -y rabbitmq-server

TMP_DIR=$HOME/tmp
if ! [ -d "$TMP_DIR" ]; then
	mkdir $TMP_DIR
fi

cd ${TMP_DIR}
wget http://download.redis.io/redis-stable.tar.gz
tar xzvf redis-stable.tar.gz
cd ${TMP_DIR}/redis-stable

make
make test
sudo make install

echo "--------------------------------------"
echo "redis configuration"
echo "--------------------------------------"
cd ${TMP_DIR}/redis-stable/utils

# interactive installation
# TODO: use default installation without need for interactions
sudo ./install_server.sh
# start at system start
sudo update-rc.d redis_6379 defaults

echo "--------------------------------------"
echo "redis cleanup"
echo "--------------------------------------"
rm ${TMP_DIR}/redis-stable.tar.gz
rm -rf ${TMP_DIR}/redis-stable
