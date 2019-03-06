import json
from insights import rule, make_pass, specs


CONTENT = """
Namespaces:
{% for k, stuff in namespaces.items() %}
    {{ k }}
    {{ stuff }}
{%- endfor %}
""".strip()


@rule(specs.Openshift.namespaces)
def report(nss):
    doc = json.loads(nss.content)
    return make_pass("DEMO", namespaces=doc)
