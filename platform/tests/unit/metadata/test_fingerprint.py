"""
Tests for fingerprint generation.
"""

from perfeng.metadata.fingerprint import generate_fingerprint


def test_fingerprint_stable():
    f1 = generate_fingerprint(
        cluster_name="cluster-a",
        k8s_version="v1.28.0",
        node_os="linux",
        container_runtime="containerd",
    )
    f2 = generate_fingerprint(
        cluster_name="cluster-a",
        k8s_version="v1.28.0",
        node_os="linux",
        container_runtime="containerd",
    )
    assert f1 == f2
    assert len(f1) == 64


def test_fingerprint_differs():
    f1 = generate_fingerprint(
        cluster_name="cluster-a",
        k8s_version="v1.28.0",
        node_os="linux",
        container_runtime="containerd",
    )
    f2 = generate_fingerprint(
        cluster_name="cluster-b",
        k8s_version="v1.28.0",
        node_os="linux",
        container_runtime="containerd",
    )
    assert f1 != f2


def test_fingerprint_excludes():
    f1 = generate_fingerprint(
        cluster_name="cluster-a",
        k8s_version="v1.28.0",
        node_os="linux",
        container_runtime="containerd",
        excludes=["cluster-a"],
    )
    f2 = generate_fingerprint(
        cluster_name="cluster-b",
        k8s_version="v1.28.0",
        node_os="linux",
        container_runtime="containerd",
        excludes=["cluster-b"],
    )
    assert f1 == f2  # because excluded parts are removed
