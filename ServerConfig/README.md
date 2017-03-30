sudo mkdir /var/www/

sudo apt-get -y install git

CD to some private directory you can write to, such as 

cd /home/ubuntu

If you don't have the repositories already, clone the two
we need, otherwise pull from them to be sure you havethe
latest content.

sudo git clone https://github.com/ProjectGadfly/ServerConfig.git
sudo git clone https://github.com/ProjectGadfly/WebServer

WARNING:  Yes, you have to run this out of the directory above!
The serverconfig.sh script remembers where it started and uses
that, and if you start if from anywhere else it won't work.

sudo chmod +x ServerConfig/serverconfig.sh
sudo ./ServerConfig/serverconfig.sh


After running the shell script:

sudo mysql_secure_installation
