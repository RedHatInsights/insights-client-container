import os
import yaml

from kubernetes import config
from kubernetes.client import ApiClient, Configuration
from openshift.dynamic import DynamicClient

from insights.core.context import ExecutionContext
from insights.core.plugins import component
from insights import datasource
from insights.util import fs
from insights.core.spec_factory import ContentProvider, mangle_command, SerializedRawOutputProvider, SpecSet
from insights.core.serde import deserializer, serializer


class KubeOutputProvider(ContentProvider):
    def __init__(self, client, **client_kwargs):
        super(KubeOutputProvider, self).__init__()
        name = "%s/%s" % (client_kwargs["api_version"], client_kwargs["kind"])
        self.cmd = name.split("/")
        self.relative_path = name if name.endswith(".yaml") else name + ".yaml"
        self.root = "/"
        self.client_kwargs = client_kwargs
        self.k8s = client.k8s

    def load(self):
        return yaml.dump(self.k8s.resources.get(**self.client_kwargs).get().to_dict())

    def write(self, dst):
        fs.ensure_path(os.path.dirname(dst))
        with open(dst, "w") as f:
            f.write(self.content)


@serializer(KubeOutputProvider)
def serialize_kube_output(obj, root):
    rel = os.path.join("k8s", *obj.cmd)
    dst = os.path.join(root, rel)
    fs.ensure_path(os.path.dirname(dst))
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
            config.load_incluster_config()  # makes a singleton config behind the scenes
            k8cfg = Configuration()  # gets a copy from what was populated in the line above
            # NOTE this is required due to https://github.com/openshift/origin/issues/22125
            k8cfg.verify_ssl = False
            k8s_client = ApiClient(configuration=k8cfg)  # this should use the singleton produced above
        self.k8s = DynamicClient(k8s_client)  # stole this from config.new_client_from_config


class kube_command(object):
    def __init__(self, kind, api_version="v1", **kwargs):
        # encode group into the api_version string if necessary
        self.client_kwargs = kwargs
        self.client_kwargs["kind"] = kind
        self.client_kwargs["api_version"] = api_version
        self.__name__ = self.__class__.__name__
        datasource(KubeClient)(self)

    def __call__(self, broker):
        client = broker[KubeClient]
        return KubeOutputProvider(client, **self.client_kwargs)


class KubeSpecs(SpecSet):
    ns_info = kube_command(kind="Namespace")
    nodes = kube_command(kind="Node")
    crds = kube_command(api_version="apiextensions.k8s.io/v1beta1", kind="CustomResourceDefinition")

    @datasource(crds, KubeClient)
    def crs(broker):
        client = broker[KubeClient]
        cr_list = []
        for crd in yaml.safe_load(broker[KubeSpecs.crds].content)["items"]:
            group = crd["spec"]["group"]
            version = crd["spec"]["version"]
            kind = crd["spec"]["names"]["kind"]
            cr_list.append(KubeOutputProvider(client, api_version="%s/%s" % (group, version), kind=kind))
        return cr_list
