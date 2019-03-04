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
fact_dict = {
    "insights_id": next(o["metadata"]["uid"] for o in doc["items"] if o["metadata"]["name"] == "kube-system")
}
print(json.dumps(fact_dict))
