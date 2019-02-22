import os
from setuptools import setup, find_packages

runtime = set([
    "insights-core",
    "openshift",
])

setup(
    name="insights_k8s",
    version="0.0.1",
    description="Kubernetes Insights Components",
    author="Red Hat, Inc.",
    author_email="insights@redhat.com",
    packages=find_packages(),
    install_requires=list(runtime),
)
