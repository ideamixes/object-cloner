"""Module that implements all cluster object logic."""
import os
import re
import time

from datetime import datetime
import dictdiffer
from mergedeep import merge
from pykube.exceptions import HTTPError, ObjectDoesNotExist

from .helpers import delete_fields
from .resources import get_namespaced_object, \
    create_namespaced_object, \
    update_namespaced_object, \
    delete_namespaced_object


class ClusterObject:
    """
    Implements all cluster object logic.
    """

    def __init__(self, body, all_namespace_names, logger):
        self.body = body
        self.all_namespace_names = all_namespace_names
        self.logger = logger

        self.namespace = self.body['metadata']['namespace']
        self.handled_object_attrs = {
            'group': self.body['spec']['sourceObject']['group'],
            'version': self.body['spec']['sourceObject']['version'],
            'kind': self.body['spec']['sourceObject']['kind'],
            'name': self.body['metadata']['name'],
        }

        self.update_strategy = self.body['spec'].get('updateStrategy', 'Default')
        if self.update_strategy == 'Default':
            self.update_strategy = os.environ.get('OBJECT_CLONER_UPDATE_STRATEGY', 'Auto')

    def get_source_object(self):
        """
        Obtain definition for the source object.

        :return: dict
        """

        source_object = get_namespaced_object(
            self.handled_object_attrs['group'],
            self.handled_object_attrs['version'],
            self.handled_object_attrs['kind'],
            self.namespace,
            self.handled_object_attrs['name']
        ).__dict__['obj']
        self.logger.debug(f'Source object: {source_object}')
        self.normalize_object(source_object)
        return source_object

    def normalize_object(self, obj):
        """
        Removes the object fields that should not be copied to a clone object.

        :param obj: source or target object to cleanup
        :return: None
        """

        fields_to_exclude = self.body['spec'].get('fieldsToExclude', []).copy()
        fields_to_exclude.append(['status'])
        fields_to_exclude.append(['metadata', 'annotations'])
        fields_to_exclude.append(['metadata', 'creationTimestamp'])
        fields_to_exclude.append(['metadata', 'managedFields'])
        fields_to_exclude.append(['metadata', 'namespace'])
        fields_to_exclude.append(['metadata', 'ownerReferences'])
        fields_to_exclude.append(['metadata', 'resourceVersion'])
        fields_to_exclude.append(['metadata', 'uid'])
        delete_fields(obj, fields_to_exclude)

    # pylint: disable=too-many-branches
    def sync_to_namespaces(self, namespace_name=None):
        """
        Sync a source object to one or more target namespaces.

        :param namespace_name: one or more target namespaces
        :type namespace_name: str, list
        :return:
        """
        namespaces_to_add_object_to = []
        namespaces_to_update_object = []
        namespace_names = self.get_target_namespace_names()
        if namespace_name is not None:
            if namespace_name in namespace_names:
                namespace_names = [namespace_name]
            else:
                return False
        try:
            source_object = self.get_source_object()
        except ObjectDoesNotExist:
            self.logger.info(
                f'''
                Cannot sync - source object {self.handled_object_attrs['group']}/{self.handled_object_attrs['version']}
                {self.handled_object_attrs['kind']} {self.handled_object_attrs['name']} is not found.
                '''
            )
            return False
        for namespace in namespace_names:
            self.logger.info(f'Target namespace: {namespace}')
            try:
                target_object = get_namespaced_object(
                    self.handled_object_attrs['group'],
                    self.handled_object_attrs['version'],
                    self.handled_object_attrs['kind'],
                    namespace,
                    self.handled_object_attrs['name']
                ).__dict__['obj']
                self.normalize_object(target_object)
                if source_object != target_object:
                    self.logger.info(
                        f"""
                        {source_object['metadata']['name']} objects in {self.namespace} and {namespace} are different:
                        """
                    )
                    for diff in dictdiffer.diff(source_object, target_object):
                        self.logger.info(diff)
                    namespaces_to_update_object.append(namespace)
            except ObjectDoesNotExist:
                namespaces_to_add_object_to.append(namespace)
        self.logger.debug(f'Source object: {source_object}')
        updated_namespaces = []
        for namespace in namespaces_to_add_object_to:
            self._create_target_object(namespace, source_object)
            updated_namespaces.append(namespace)
        for namespace in namespaces_to_update_object:
            if self.update_strategy == 'AlwaysRecreate':
                self._recreate_target_object(namespace, source_object)
                updated_namespaces.append(namespace)
            else:
                patch_result = self._patch_target_object(namespace, source_object)
                if patch_result:
                    updated_namespaces.append(namespace)
        self.update_namespace_sync_status(updated_namespaces)
        return True

    def update_namespace_sync_status(self, namespaces, delete=False):
        """
        Update syncedNamespaces list in the status subresource.

        :param namespaces:
        :param delete: Whether to remove the namespace from the list
        :return:
        """
        now = datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')
        if self.body['status'].get('syncedNamespaces') is None:
            self.body['status']['syncedNamespaces'] = []
        for namespace in namespaces:
            for namespace_status in self.body['status']['syncedNamespaces']:
                if namespace_status['name'] == namespace:
                    if delete:
                        self.body['status']['syncedNamespaces'].remove(namespace_status)
                    else:
                        namespace_status['timestamp'] = now
                    break
            else:
                if not delete:
                    self.body['status']['syncedNamespaces'].append({
                        'name': namespace,
                        'timestamp': now
                    })
        version, group = [e[::-1] for e in (self.body['apiVersion'][::-1] + '/').split('/')[0:2]]
        update_namespaced_object(
            group,
            version,
            self.body['kind'],
            self.namespace,
            self.body,
            subresource='status'
        )

    def _patch_target_object(self, namespace, source_object):
        for _ in range(10):
            target_object = get_namespaced_object(
                self.handled_object_attrs['group'],
                self.handled_object_attrs['version'],
                self.handled_object_attrs['kind'],
                namespace,
                self.handled_object_attrs['name']
            ).__dict__['obj']
            try:
                merge(target_object, source_object)
                update_namespaced_object(
                    self.handled_object_attrs['group'],
                    self.handled_object_attrs['version'],
                    self.handled_object_attrs['kind'],
                    namespace,
                    target_object
                )
            except HTTPError as err:
                if err.code == 409:
                    self.logger.warning(f'Object update conflict: {err}. Retrying...')
                    time.sleep(2)
                    continue
                if err.code == 422:
                    if target_object['immutable']:
                        self.logger.info(
                            f'immutable field for the {target_object["metadata"]["name"]} object is set to True: {err}'
                        )
                    else:
                        self.logger.info(
                            f'''immutable field for the {target_object["metadata"]["name"]} object is set to False 
                            but we still got 422: {err}
                            '''
                        )
                    if self.update_strategy == 'NeverRecreate':
                        self.logger.info('Cannot updated the object - recreation is disabled.')
                        return False
                    self.logger.info('Recreating the object...')
                    self._recreate_target_object(namespace, source_object, target_object)
                    break
                raise
            break
        return True

    def _create_target_object(self, namespace, source_object):
        create_namespaced_object(
            self.handled_object_attrs['group'],
            self.handled_object_attrs['version'],
            self.handled_object_attrs['kind'],
            namespace,
            source_object
        )

    def _recreate_target_object(self, namespace, source_object, target_object=None):
        if target_object is None:
            target_object = get_namespaced_object(
                self.handled_object_attrs['group'],
                self.handled_object_attrs['version'],
                self.handled_object_attrs['kind'],
                namespace,
                self.handled_object_attrs['name']
            ).__dict__['obj']
        delete_namespaced_object(
            self.handled_object_attrs['group'],
            self.handled_object_attrs['version'],
            self.handled_object_attrs['kind'],
            namespace,
            target_object
        )
        create_namespaced_object(
            self.handled_object_attrs['group'],
            self.handled_object_attrs['version'],
            self.handled_object_attrs['kind'],
            namespace,
            source_object
        )

    def delete_all_target_objects(self):
        """
        Clean up all target objects.

        :return:
        """
        synced_namespaces = [ns_status['name'] for ns_status in self.body['status'].get('syncedNamespaces', [])]
        for namespace in synced_namespaces:
            try:
                target_object = get_namespaced_object(
                    self.handled_object_attrs['group'],
                    self.handled_object_attrs['version'],
                    self.handled_object_attrs['kind'],
                    namespace,
                    self.handled_object_attrs['name']
                ).__dict__['obj']
            except ObjectDoesNotExist as err:
                self.logger.warning(f'Object does not exist: {err}')
                continue
            delete_namespaced_object(
                self.handled_object_attrs['group'],
                self.handled_object_attrs['version'],
                self.handled_object_attrs['kind'],
                namespace,
                target_object
            )



    def get_target_namespace_names(self):
        """
        List all existing namespaces that satisfy object filters.

        :return: list of namespace names
        """
        namespaces_to_include = self.body['spec'].get('namespacesToInclude', ['.*'])
        namespaces_to_exclude = self.body['spec'].get('namespacesToExclude', []) + [self.body['metadata']['namespace']]
        namespaces_names = []
        for namespace in self.all_namespace_names:
            for ns_to_include in namespaces_to_include:
                if re.match(ns_to_include, namespace):
                    for ns_to_exclude in namespaces_to_exclude:
                        if re.match(ns_to_exclude, namespace):
                            break
                    else:
                        namespaces_names.append(namespace)
                        break
                    break
        return namespaces_names
