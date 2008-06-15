#!/bin/bash

DATE=`date +%Y%m%d`
YUM_CONF_LOC=/etc/yum.repos.d/yum.epel.conf
OUTPUT_DIR=$HOME
RC_REPORT_CFG=/etc/rc-report-epel.cfg

process_deps()
{
    release=$1
    arch=$2
    testing=$3
    mail=$4
    [ -z $4 ] && mail="no" || mail="yes"
    [ $arch = "ppc" ] && arch_label=ppc64 || arch_label=$arch
    command="/usr/local/bin/rc-modified -d mdcache -n -c $YUM_CONF_LOC -a $arch_label -r rhel-$release-$arch -r fedora-epel-$release-$arch"
    [ $release -eq 5 ] && command="$command -r rhel-$release-$arch-vt "
    [ "$testing" =  "testing" ] && command="$command -r fedora-epel-testing-$release-$arch "
    OUTFILE=$OUTPUT_DIR/epel${release}${arch}-$DATE.txt
    $command > $OUTFILE
    [ "$4" = "yes" ] && /usr/local/bin/rc-report.py $OUTFILE -k epel -c $RC_REPORT_CFG -w testing -m summary -m owner
}


# process_deps RHEL_RELEASE ARCH INCLUDE_TESTING? MAIL?

# RHEL 5
process_deps 5 i386 testing yes
process_deps 5 x86_64 testing yes
process_deps 5 ppc testing yes

# RHEL 4
process_deps 4 i386 testing yes
process_deps 4 x86_64 testing yes
process_deps 4 ppc testing yes
