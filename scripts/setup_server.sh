#!/usr/bin/env bash
#####################################################
#
# Required setup for server
# - Ubuntu 16.04
# - apache2
#
#####################################################


# docker installation

# docker-compose
cd $HOME
curl -L https://github.com/docker/compose/releases/download/1.8.1/docker-compose-`uname -s`-`uname -m` > docker-compose
sudo mv docker-compose /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose