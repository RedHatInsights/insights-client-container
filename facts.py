#!/usr/bin/env python36
import sys
import yaml
import json
from insights import dr
from insights.specs.openshift import OpenshiftContext
from insights.specs.openshift.default import OpenshiftSpecs

broker = dr.Broker()
ctx = OpenshiftContext()
broker[OpenshiftContext] = ctx
b = dr.run(OpenshiftSpecs.openshift_namespaces, broker)
doc = yaml.safe_load(b[OpenshiftSpecs.openshift_namespaces].content)
for o in doc["items"]:
    if o["metadata"]["name"] == "kube-system":
        print(json.dumps({"insights_id": o["metadata"]["uid"]}))
        sys.exit(0)
sys.exit(1)
