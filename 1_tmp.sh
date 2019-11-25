#!/bin/bash  
if [ -f ~/.bash_profile ];
then
. ~/.bash_profile
fi

sqlplus hgame/ora_0046 <<EOF
set serveroutput on
set echo on
set feedback on
set timing on
exec p_agent_bet_recharge('20170926','20171012');
quit;
EOF

