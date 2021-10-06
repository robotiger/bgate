sudo apt update
sudo apt upgrade

sudo apt install nginx
#sudo cp nginx.conf /etc/nginx/nginx.conf 
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
sudo cp 99-gpio.rules /etc/udev/rules.d/
sudo groupadd gpio
sudo usermod -aG gpio bfg

pip3 install OPi.GPIO 
#pip3 install setuptools==21.2.1
pip3 install setuptools
pip3 install wheel gunicorn flask #проверить порядок установки
pip3 install requests
pip3 install pyserial
pip3 install paho-mqtt
pip3 install msgpack
pip3 install pyserial
pip3 install pycryptodome
pip3 install werkzeug
pip3 install nmcli
pip3 install pyzmq
sudo apt install gunicorn3
sudo apt install libzmq3-dev
sudo apt install dnsmasq-base
sudo cp shutdown.allow /etc
sudo cp bgate.service /etc/systemd/system
sudo systemctl enable bgate.service


#sudo cp barry.conf /etc/nginx/sites-available
#sudo ln -s /etc/nginx/sites-available/barry.conf /etc/nginx/sites-enabled/
#sudo cp favicon.ico /var/www/barry/www
#sudo apt install ffmpeg
#sudo apt install python3-dev
#sudo apt install python3-opencv
#pip3 install rtsp














