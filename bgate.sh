#git pull
if [ ! -f /home/bfg/bgate/config.db ]; then 
  /home/bfg/bgate/startwifi.sh
fi
python3 bfgate.py
if [ -f /home/bfg/bgate/extcommand.sh ]; then 
   /home/bfg/bgate/extcommand.sh
   rm /home/bfg/bgate/extcommand.sh
fi


