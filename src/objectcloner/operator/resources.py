"""Kubernetes API operations."""
import pykube

from .kubeapi import kubernetes_api


@kubernetes_api
# pylint: disable=too-many-arguments
def get_namespaced_object(api, group, version, kind, namespace, name):
    """
    Obtains API object in the given namespace.

    :param api:
    :param group:
    :param version:
    :param kind:
    :param namespace:
    :param name:
    :return:
    """
    kind = pykube.object_factory(api, f"{group}{'/' if group != '' else ''}{version}", kind)
    return kind.objects(api).filter(namespace).get(name=name)


@kubernetes_api
# pylint: disable=too-many-arguments
def create_namespaced_object(api, group, version, kind, namespace, obj):
    """
    Create API object in the given namespace.

    :param api:
    :param group:
    :param version:
    :param kind:
    :param namespace:
    :param obj:
    :return:
    """
    obj['metadata']['namespace'] = namespace
    kind = pykube.object_factory(api, f"{group}{'/' if group != '' else ''}{version}", kind)
    return kind(api, obj).create()


@kubernetes_api
# pylint: disable=too-many-arguments
def update_namespaced_object(api, group, version, kind, namespace, obj, subresource=None):
    """
    Updates API object in the given namespace.

    :param subresource:
    :param api:
    :param group:
    :param version:
    :param kind:
    :param namespace:
    :param obj:
    :return:
    """
    obj['metadata']['namespace'] = namespace
    print(f'XXXXXXXXXXXXXX: {obj}')
    kind = pykube.object_factory(api, f"{group}{'/' if group != '' else ''}{version}", kind)
    return kind(api, obj).update(subresource=subresource)


@kubernetes_api
# pylint: disable=too-many-arguments
def delete_namespaced_object(api, group, version, kind, namespace, obj):
    """
    Deletes API object from the given namespace.

    :param api:
    :param group:
    :param version:
    :param kind:
    :param namespace:
    :param obj:
    :return:
    """
    obj['metadata']['namespace'] = namespace
    kind = pykube.object_factory(api, f"{group}{'/' if group != '' else ''}{version}", kind)
    return kind(api, obj).delete()
