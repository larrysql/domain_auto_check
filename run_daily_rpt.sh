#!/bin/bash  
if [ -f ~/.bash_profile ];   
then  
. ~/.bash_profile  
fi  

begin_day=`date  +"%Y%m%d" -d  "-1 days"`
end_day=`date  +"%Y%m%d" -d  "-1 days"`
sqlplus hgame/ora_0046 <<EOF
set serveroutput on
set echo on
set feedback on
set timing on
exec dbms_refresh.refresh('HGAME.ref_agent_tree_grp');
exec p_agent_bet_recharge('$begin_day','$end_day');
exec p_other_stat_d('$begin_day','$end_day');
quit;
EOF
