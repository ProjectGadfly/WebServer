#!/bin/bash
# WARNING:
# -> Must be run exactly in accordance with the instructions in README.md in ServerConfig Resp
# If any of the commands fail, script will abort
set -e
# ensure this script is running at root 
if [[ $(id -u) -ne 0 ]]; then
    echo ERROR: SCRIPT MUST BE RUN AS ROOT!
    exit 2
fi
origdir=$PWD
echo "installing needed packages"
apt-get -y install apache2 libapache2-mod-wsgi-py3  python3.5 python3.5-venv python3-pip mysql-server python-mysqldb libmysqlclient-dev mysql-client-5.7
echo "Packages installed"
# /var/www/GFServer cleanout
rm -rf /var/www/GFServer
mkdir -p /var/www/GFServer
echo "moving files to GFServer"
# if below command returns a non-zero statues, then run /bin/true/ 
cp ../ServerConfig/* /var/www/GFServer/ || true
echo ""
# replace existing python module with current (resp) version
mkdir -p /var/www/GFServer/services
cp GFServer.py /var/www/GFServer/services
cp ServerConfig/services/GFServer.wsgi /var/www/GFServer/services
echo "Make New Python virtualenv"
cd /var/www/GFServer/
virtualenv -p /usr/bin/python3 flaskappenv
source flaskappenv/bin/activate
pip install -r $origdir/requirements.txt
echo "moving Apache config into place"
cp $origdir/ServerConfig/services/GFServer.conf /etc/apache2/sites-available/
sed -i '1 a\127.0.0.1       GFServer' /etc/hosts
# remove ubuntu apache package default site 
rm -f /etc/apache2/sites-enabled/000-default.conf
echo "restarting Apache"
a2ensite GFServer
service apache2 restart
echo "Script complete. Please check the server's IP in your browser"
