"""Kopf handlers."""
import os
import time

import kopf

from .clusterobject import ClusterObject


@kopf.index('', 'v1', 'Namespace')
def idx_namespace_names(name: str, **_):
    """
    Index for all namespace names

    :param name:
    :param _:
    :return:
    """
    return name


@kopf.index('object-cloner.ideamix.es', 'v1', 'ClusterObject')
# pylint: disable=redefined-outer-name
def idx_handled_dynamic_objects(name, namespace, body, idx_namespace_names, logger, **_):
    """
    Index for all source objects handled by the operator.

    :param name:
    :param namespace:
    :param body:
    :param idx_namespace_names:
    :param logger:
    :param _:
    :return:
    """
    source_object_group = body['spec']['sourceObject']['group']
    source_object_version = body['spec']['sourceObject']['version']
    source_object_kind = body['spec']['sourceObject']['kind']
    # pylint: disable=redefined-outer-name
    while len(idx_namespace_names) == 0:
        logger.info('idx_namespace_names has not been initialized yet. Sleeping...')
        time.sleep(1)
    logger.info(idx_namespace_names)
    cluster_object = ClusterObject(body, idx_namespace_names[None], logger)
    return {(source_object_group, source_object_version, source_object_kind, namespace, name): cluster_object}


# pylint: disable=redefined-outer-name
def is_of_interest(resource, namespace, name, idx_handled_dynamic_objects, **_):
    """
    Check if an object is handled by the operator.

    :param resource:
    :param namespace:
    :param name:
    :param idx_handled_dynamic_objects:
    :param _:
    :return:
    """
    return (resource.group, resource.version, resource.kind, namespace, name) in idx_handled_dynamic_objects


@kopf.on.resume('object-cloner.ideamix.es', 'v1', 'ClusterObject')
@kopf.on.create('object-cloner.ideamix.es', 'v1', 'ClusterObject')
@kopf.on.update('object-cloner.ideamix.es', 'v1', 'ClusterObject')
# pylint: disable=redefined-outer-name
def on_create_update_clusterobject(spec, name, namespace, idx_handled_dynamic_objects, **_):
    """
    Sync cluster object on creation on update.

    :param spec:
    :param name:
    :param namespace:
    :param idx_handled_dynamic_objects:
    :param _:
    :return:
    """
    cluster_object_store = idx_handled_dynamic_objects.get((
        spec['sourceObject']['group'],
        spec['sourceObject']['version'],
        spec['sourceObject']['kind'],
        namespace,
        name
    ), [])
    for cluster_object in cluster_object_store:
        cluster_object.sync_to_namespaces()


@kopf.on.delete('object-cloner.ideamix.es', 'v1', 'ClusterObject')
# pylint: disable=redefined-outer-name
def on_delete_clusterobject(body, idx_namespace_names, logger, **_):
    """
    Sync cluster object on creation on update.

    :param spec:
    :param name:
    :param namespace:
    :param idx_handled_dynamic_objects:
    :param _:
    :return:
    """
    cluster_object = ClusterObject(body, idx_namespace_names[None], logger)
    if 'OnClusterObjectDelete' in body['spec'].get('cleanupEvents', '').split(','):
        cluster_object.delete_all_target_objects()


@kopf.on.create('', 'v1', 'Namespace')
# pylint: disable=redefined-outer-name
def on_create_namespace(name, idx_handled_dynamic_objects, **_):
    """
    Create target objects in the namespace on its creation.

    :param name:
    :param idx_handled_dynamic_objects:
    :param _:
    :return:
    """
    for _, cluster_object_store in idx_handled_dynamic_objects.items():
        for cluster_object in cluster_object_store:
            cluster_object.sync_to_namespaces(name)


@kopf.on.delete('', 'v1', 'Namespace')
# pylint: disable=redefined-outer-name
def on_delete_namespace(name, idx_handled_dynamic_objects, **_):
    """
    Remove the namespace from the list of synced ones.

    :param name:
    :param idx_handled_dynamic_objects:
    :param _:
    :return:
    """
    for _, cluster_object_store in idx_handled_dynamic_objects.items():
        for cluster_object in cluster_object_store:
            cluster_object.update_namespace_sync_status(name, delete=True)


def create_sourceobject_handlers():
    """
    Dynamically create handlers for handled source objects.

    :return:
    """
    allowed_object_kinds = os.environ.get('OBJECT_CLONER_ALLOWED_OBJECT_KINDS')
    kind_selectors = []
    if allowed_object_kinds is not None:
        for allowed_object_kind in allowed_object_kinds.split(" "):
            if len(allowed_object_kind) == 0:
                continue
            kind_selectors.append(allowed_object_kind.split(","))
    else:
        kind_selectors.append([kopf.EVERYTHING])

    for kind_selector in kind_selectors:
        # pylint: disable=cell-var-from-loop
        @kopf.on.create(*kind_selector, when=is_of_interest)
        # pylint: disable=cell-var-from-loop
        @kopf.on.update(*kind_selector, when=is_of_interest)
        def on_create_update_sourceobject(resource, name, namespace, idx_handled_dynamic_objects, **_):
            cluster_object_store = idx_handled_dynamic_objects.get(
                (resource.group, resource.version, resource.kind, namespace, name), [])
            for cluster_object in cluster_object_store:
                cluster_object.sync_to_namespaces()

        # pylint: disable=cell-var-from-loop
        @kopf.on.delete(*kind_selector, when=is_of_interest)
        def on_delete_sourceobject(resource, name, namespace, idx_handled_dynamic_objects, **_):
            cluster_object_store = idx_handled_dynamic_objects.get(
                (resource.group, resource.version, resource.kind, namespace, name), [])
            for cluster_object in cluster_object_store:
                if 'OnSourceObjectDelete' in cluster_object.body['spec'].get('cleanupEvents', '').split(','):
                    cluster_object.delete_all_target_objects()


create_sourceobject_handlers()
