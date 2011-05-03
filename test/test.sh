#!/bin/sh
#
# The first test attempts to model the actual running configuration
# that we'll use if we want to keep BuildBot's droppings out of our
# source tree: a symlink to master.cfg in the parent directory.  See
# __init__.py for more details about the reasons for this

set -e

for x in memoize platform procedures slave status ; do
    python ../$x.py
done

buildbot checkconfig
buildbot create-master

echo '************** START ***************'
buildbot start || (buildbot stop ; exit 1)
sleep 1
echo '************** RECONFIG ***************'
buildbot reconfig || (buildbot stop ; exit 1)
sleep 1
echo '************** STOP ***************'
buildbot stop

# Clean up the source directory
rm -rf *.sample public_html state.sqlite twistd.log buildbot.tac project*

# It's also desirable to be able to run checkconfig directly from the
# root of the source tree during development, using an unmodified
# source tree and adding no symlinks, so we'll test again.
echo '#################'

cd bbot_test
buildbot checkconfig

