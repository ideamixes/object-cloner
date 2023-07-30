# object-cloner

Allows to copy namespaced objects to other namespaces and keep them synced. All object kinds are supported, for example 
Secret, ConfigMap.

## Installation

* [Helm chart](./deploy/helm-object-cloner/README.md)

## Configuration

The following environment variables can be set:

| Name                               | Default Value | Description                                                                                                                                                                                                                                                                                                                                                                                   |
|------------------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| OBJECT_CLONER_LOG_LEVEL            | INFO          | Log level                                                                                                                                                                                                                                                                                                                                                                                     |
| OBJECT_CLONER_ALLOWED_OBJECT_KINDS | ,v1,secrets   | A space-delimited list of object kind definitions. Each definition consists of 3 comma-delimited items: API group, version, Kind plural. The setting is used to limit number of resources that the operator manages both performance- and security-wise. If unset, the operator will watch all objects.                                                                                       |
| OBJECT_CLONER_UPDATE_STRATEGY      | Auto          | Defines the way how the clone objects are updated:<br/>* `Auto` - will try to patch the object first and fall back to recreation if the object is immutable or the updated specification cannot be processed<br/>* `AlwaysRecreate` - will re-create the object for any update<br/>* `NeverRecreate` - will try to patch the object and, if the patch is failed, will not try to recreate it. |

## Usage

[`ClusterObject` CRD](./deploy/helm-object-cloner/templates/crd.yaml) allows creating the namespaced objects that 
linked to a source object in the same namespace and defines rules how the source object should be cloned and synced in 
other namespaces.

### Minimal Example

```yaml
---
kind: ClusterObject
apiVersion: object-cloner.ideamix.es/v1
metadata:
  name: acr-credentials
spec:
  namespacesToInclude:
    - '.*'
  sourceObject:
    group: ''
    version: v1
    kind: Secret
```

### Supported Fields

| Field                        | Type          | Required | Default Value                                  | Description                                                                                                                                                                                                                                                                                                                                                               |
|------------------------------|---------------|----------|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `.spec.sourceObject.group`   | string        | yes      |                                                | API group of the source object                                                                                                                                                                                                                                                                                                                                            |
| `.spec.sourceObject.version` | string        | yes      |                                                | API version of the source object                                                                                                                                                                                                                                                                                                                                          |
| `.spec.sourceObject.kind`    | string        | yes      |                                                | The source object's Kind                                                                                                                                                                                                                                                                                                                                                  |
| `.spec.sourceObject.name`    | string        | no       | `.metadata.name` of the `ClusterObject` object | Name of the source object                                                                                                                                                                                                                                                                                                                                                 |
| `.spec.namespacesToInclude`  | array[string] | yes      |                                                | A ist of the namespaces where the source object should be cloned to. Items may contain [Python's regular expressions](https://docs.python.org/3/library/re.html) which allows to expand them into zero or more existing namespace names.                                                                                                                                  |
| `.spec.namespacesToExclude`  | array[string  | no       | []                                             | A list of the namespaces where the source object should not be cloned to. Items may contain [Python's regular expressions](https://docs.python.org/3/library/re.html) which allows to expand them into zero or more existing namespace names.                                                                                                                             |
| `.spec.fieldsToExclude`      | array[string] | no       | []                                             | The source object's fields that should not be cloned. Each field can defined as a path to it in the specification, for example `.metadata.labels`. `.status` and some `.metadata` fields are never cloned.                                                                                                                                                                |
| `.spec.cleanupEvents`        | string        | no       | ""                                             | A comma-delimited list that defines how clone objects are cleaned up.<br/>* `OnClusterObjectDelete` - when `ClusterObject` is deleted<br/>* `OnSourceObjectDelete` - when the source object is deleted<br/>* `OnClusterObjectDelete,OnSourceObjectDelete` - when either `ClusterObject` object or source object is deleted<br/>* "" - the clone objects are never deleted |
| `.spec.updateStrategy`       | string        | no       | Default                                        | See information for the `OBJECT_CLONER_UPDATE_STRATEGY` environment variable above. `Default` value instructs to use the value set by `OBJECT_CLONER_UPDATE_STRATEGY`.                                                                                                                                                                                                    |


## Development

```shell
# Install
virtualenv /path/to/object-cloner-venv
. /path/to/object-cloner-venv/bin/activate
OBJECT_CLONER_DEV_DEPENDENCIES_ENABLED=true pip install src/

# Run
KUBECONFIG=/path/to/kubeconfig kopf run -v -A -m objectcloner
```
