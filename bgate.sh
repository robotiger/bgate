#git pull
test -f /home/bfg/bgate/config.db && /home/bfg/bgate/startwifi.sh
python3 bfgate.py
test -f /home/bfg/bgate/extcommand.sh && /home/bfg/bgate/extcommand.sh


