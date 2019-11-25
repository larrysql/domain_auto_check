#!/bin/bash  
if [ -f ~/.bash_profile ];   
then  
. ~/.bash_profile  
fi 

sqlplus hgame/ora_0046<<EOF
exec dbms_refresh.refresh('HGAME.ref_agent_tree_grp');
quit;
EOF
