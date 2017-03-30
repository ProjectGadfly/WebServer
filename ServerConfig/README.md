sudo mkdir /var/www/

sudo apt-get -y install git

CD to some private directory you can write to, such as 

cd /home/ubuntu

If you don't have the repositorys already, clone it, otherwise pull
from them to be sure you have the latest content.

sudo git clone https://github.com/ProjectGadfly/WebServer

Cd into the repo.

cd WebServer

(Yes you have to run it from up here!)

sudo -H ./ServerConfig/serverconfig.sh


After running the shell script:

sudo mysql_secure_installation

and run the sql to init the database