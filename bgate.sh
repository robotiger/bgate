#git pull
[ ! -f /home/bfg/bgate/config.db]; && /home/bfg/bgate/startwifi.sh
python3 bfgate.py
[ -f /home/bfg/bgate/extcommand.sh]; && /home/bfg/bgate/extcommand.sh


