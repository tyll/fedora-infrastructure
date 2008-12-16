#!/bin/bash

DATE=`date +%Y%m%d`
YUM_CONF_LOC=/etc/yum.repos.d/yum.epel.conf
OUTPUT_DIR=$HOME
RC_REPORT_CFG=/etc/rc-report-epel.cfg
PATH=$PATH:.:/usr/local/bin

OUTFILE=/tmp/epel-deps-$DATE.txt
>$OUTFILE

SEND_EMAIL="yes"


process_deps()
{
    release=$1
    arch=$2
    testing=$3
    [ $arch = "ppc" ] && arch_label=ppc64 || arch_label=$arch
    [ $arch = "i386" ] && arch_label=i686  || arch_label=$arch
    command="rc-modified -q -d mdcache -n -c $YUM_CONF_LOC -a $arch_label -r rhel-$release-$arch -r fedora-epel-$release-$arch -r buildsys-$release-$arch -r rhel-$arch-server-productivity-$release"
    [ $release -eq 5 ] && command="$command -r rhel-$release-$arch-vt "
    [ "$testing" =  "testing" ] && command="$command -r fedora-epel-testing-$release-$arch "
    $command >> $OUTFILE
}

mailer()
{
    rc-report.py $OUTFILE -k epel -c $RC_REPORT_CFG -w testing -m summary -m owner
}

# process_deps RHEL_RELEASE ARCH INCLUDE_TESTING? 

# RHEL 5
process_deps 5 i386 testing 
process_deps 5 x86_64 testing
process_deps 5 ppc testing 

# RHEL 4
process_deps 4 i386 testing 
process_deps 4 x86_64 testing 
process_deps 4 ppc testing 

if [ "$SEND_EMAIL" = "yes" ] ; then
   mailer
fi
