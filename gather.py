#!/usr/bin/env python3.6
import os
import yaml

from kubernetes import config
from kubernetes.client import ApiClient, Configuration
from openshift.dynamic import DynamicClient

from insights.core.context import ExecutionContext
from insights.core.plugins import component
from insights import rule, make_pass
from insights.util import fs
from insights.core.spec_factory import ContentProvider, mangle_command, SerializedRawOutputProvider
from insights.core.serde import deserializer, serializer


CONTENT = """
Namespaces:
{% for k, stuff in namespaces.items() %}
    {{ k }}
    {{ stuff }}
{%- endfor %}
""".strip()


class KubeOutputProvider(ContentProvider):
    def __init__(self, content, name):
        super(KubeOutputProvider, self).__init__()
        self.cmd = name
        self.relative_path = name if name.endswith(".yaml") else name + ".yaml"
        self._content = content
        self.root = "/"

    def load(self):
        return self._content

    def write(self, dst):
        fs.ensure_path(os.path.dirname(dst))
        with open(dst, "w") as f:
            f.write(self.content)


@serializer(KubeOutputProvider)
def serialize_kube_output(obj, root):
    rel = os.path.join("insights_commands", mangle_command(obj.cmd))
    dst = os.path.join(root, rel)
    obj.write(dst)
    return {
        "cmd": obj.cmd,
        "args": obj.args,
        "relative_path": rel
    }


@deserializer(KubeOutputProvider)
def deserialize_kube_output(_type, data, root):
    rel = data["relative_path"]
    res = SerializedRawOutputProvider(rel, root)
    res.cmd = data["cmd"]
    res.args = data["args"]
    return res


class KubeContext(ExecutionContext):
    pass


@component(KubeContext)
class KubeClient(object):
    def __init__(self, ctx=None, cfg=None):
        cfg = cfg or os.environ.get("KUBECONFIG")
        if cfg:
            k8s_client = config.new_client_from_config(cfg)
        else:
            # TODO not sure about this bit
            # TODO this is a mess, looks like self-signed certs will not verify properly in python
            config.load_incluster_config()  # makes a singleton config behind the scenes
            k8cfg = Configuration()  # gets a copy from what was populated in the line above
            k8cfg.verify_ssl = False
            k8s_client = ApiClient(configuration=k8cfg)  # this should use the singleton produced above
        self.client = DynamicClient(k8s_client)  # stole this from config.new_client_from_config


class kube_command(component):
    requires = [KubeClient]


@kube_command()
def get_node_names(k8s):
    val = k8s.client.resources.get(api_version="v1", kind="Node").get()
    return KubeOutputProvider(yaml.dump([n["metadata"]["name"] for n in val.to_dict()["items"]]), "node_names")


@kube_command()
def get_ns_info(k8s):
    val = k8s.client.resources.get(api_version="v1", kind="Namespace").get().to_dict()
    return KubeOutputProvider(yaml.dump(val), "namespaces")


@rule(get_ns_info)
def report(nss):
    doc = yaml.safe_load(nss.content)
    return make_pass("K8S_NODES", namespaces=doc)


if __name__ == "__main__":
    from insights.collect import collect
    with open("/usr/share/manifest.yaml") as f:
        doc = yaml.safe_load(f)
    print(collect(doc, compress=True))
