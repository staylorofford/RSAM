#!/bin/bash

#run by crontab to make 10 min rsam files

function usage(){
cat <<EOF
Usage: $0 [Options]  

Options:
    -h              Show this message.
    -d              Pass a different date using the format yyyymmdd
EOF
}

date=`date -u +%Y%m%d`

# Processing command line options
while [ $# -gt 0 ]
    do
        case "$1" in 
	    -d) date="$2";shift;;
	    -h) usage; exit 0;;
	    -*) usage; exit 1;;
             *) break;;
	esac
	shift	
    done

echo processing date: $date

#WSRZ.10-HHZ.RT
python ./rsam_fdsn.py WSRZ.10-HHZ.NZ ./sds $date ./workdir resp bp 2 5

#WIZ.10-HHZ.RT
python ./rsam_fdsn.py WIZ.10-HHZ.NZ ./sds $date ./workdir resp bp 2 5
