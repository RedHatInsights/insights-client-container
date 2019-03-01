import yaml

from insights import rule, make_pass
from insights.specs.openshift.default import OpenshiftSpecs


CONTENT = """
Namespaces:
{% for k, stuff in namespaces.items() %}
    {{ k }}
    {{ stuff }}
{%- endfor %}
""".strip()


@rule(OpenshiftSpecs.openshift_namespaces)
def report(nss):
    doc = yaml.safe_load(nss.content)
    return make_pass("K8S_NODES", namespaces=doc)
