import yaml

from insights import rule, make_pass
from insights_k8s.specs import KubeSpecs


CONTENT = """
Namespaces:
{% for k, stuff in namespaces.items() %}
    {{ k }}
    {{ stuff }}
{%- endfor %}
""".strip()


@rule(KubeSpecs.ns_info)
def report(nss):
    doc = yaml.safe_load(nss.content)
    return make_pass("K8S_NODES", namespaces=doc)
