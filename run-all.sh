#!/bin/bash

export THIS_DIR=$(cd $(dirname $0); pwd)
source ${THIS_DIR}/path.sh 

yes | cp -L -f ${THIS_DIR}/favicon.ico ~/www
yes | cp -L -f ${THIS_DIR}/templates/ner-home.html ~/www
yes | cp -R -L -f ${THIS_DIR}/static ~/www

sed -e "s/image/$(hostname)/g" ${THIS_DIR}/info.php > ~/www/info.php 
chmod 755 ~/www/info.php

rm -f ~/www/static/js/ner-core.js
sed -e "s/url: '\/'/url: 'info.php'/g" static/js/ner-core.js > ~/www/static/js/ner-core.js

GivePerm ~/www
INFO "permission granted"

INFO "start to trilingual instances"
parallel -j3 -env ${THIS_DIR}/server.sh ::: eng cmn spa