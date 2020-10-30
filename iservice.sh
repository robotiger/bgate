


sudo cp bgate.conf /etc/nginx/sites-available
sudo ln -s /etc/nginx/sites-available/bgate.conf /etc/nginx/sites-enabled/
sudo cp favicon.ico /var/www/

sudo cp bgate.service /etc/systemd/system
sudo systemctl enable bgate.service












