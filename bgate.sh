#git pull
if [ -f /home/bfg/bgate/ecmd ]; then 
   rm /home/bfg/bgate/ecmd
fi
if [ ! -f /home/bfg/bgate/config.db ]; then 
  /home/bfg/bgate/startwifi.sh
fi
python3 bfgate.py
if [ -f /home/bfg/bgate/extcommand.sh ]; then 
   /home/bfg/bgate/ecmd
   rm /home/bfg/bgate/ecmd
fi


