#!/usr/bin/env bash
################################################################################
# Synchronize changes in app with server.
# SSH access to server is required.
# ! do not commit any private data/password/codes in the repository !
################################################################################
# Server-Name: http://128.208.19.131/
# Login: konimatt
# Heimatverz.: /home/konigmatt
# WWW-Verz.: /var/www/html
################################################################################

rsync -rtvuc --delete ./teweb/ konigmatt@128.208.19.131:/home/konigmatt

# after synchronization



