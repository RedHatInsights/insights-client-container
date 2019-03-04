#!/bin/sh -x

# TODO manifest
# TODO CLOUDSERVICES url 
# TODO add _special_ content type
NETRC=/tmp/netrc/netrc
EGG_URL=https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg
EGG_DST=/tmp/insights-core.egg

curl --netrc-file $NETRC $EGG_URL -o $EGG_DST

TARPATH=$(PYTHONPATH=$EGG_DST insights-collect -m ${INSIGHTS_MANIFEST:-/usr/share/manifest.yaml})
CANONICAL_FACTS=$(${FACTS_SCRIPT:-/facts.py} 2>/dev/null)

curl -X POST --netrc-file $NETRC -f file=@${TARPATH} -f metadata='${CANONICAL_FACTS}' $CLOUD_SERVICES_URL
