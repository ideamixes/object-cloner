# object-cloner

Allows to copy namespaced objects to other namespaces and keep them synced. All object kinds are supported, for example 
Secret, ConfigMap.

## Installation

* [Helm chart](./deploy/helm-object-cloner/README.gotmpl.md)

## Configuration

The following environment variables can be set:

| Name                               | Default Value | Description                                                                                                                                                                                                                                                                                             |
|------------------------------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| OBJECT_CLONER_LOG_LEVEL            | INFO          | Log level                                                                                                                                                                                                                                                                                               |
| OBJECT_CLONER_ALLOWED_OBJECT_KINDS | ,v1,secrets   | A space-delimited list of object kind definitions. Each definition consists of 3 comma-delimited items: API group, version, Kind plural. The setting is used to limit number of resources that the operator manages both performance- and security-wise. If unset, the operator will watch all objects. |

## Development

```shell
# Install
virtualenv /path/to/object-cloner-venv
. /path/to/object-cloner-venv/bin/activate
OBJECT_CLONER_DEV_DEPENDENCIES_ENABLED=true pip install src/

# Run
KUBECONFIG=/path/to/kubeconfig kopf run -v -A -m objectcloner
```