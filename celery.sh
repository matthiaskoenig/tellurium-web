
CELERYD_NODES="worker1"
CELERY_BIN="/home/mkoenig/envs/tellurium_webapp/bin/celery"
CELERYD_CHDIR="/var/git/tellurium-web/teweb"
CELERYD_OPTS="--time-limit=300 --concurrency=8"
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_USER="mkoenig"
CELERYD_GROUP="mkoenig"
CELERY_CREATE_DIRS=1
CELERY_APP="teweb"

sh -c ${CELERY_BIN} multi start ${CELERYD_NODES} -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}


celery -A teweb worker -l info
