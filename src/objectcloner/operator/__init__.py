# pylint: disable=missing-module-docstring
import kopf

from .handlers import *


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    """
    Configure operator.

    :param settings:
    :param _:
    :return:
    """
    settings.persistence.finalizer = 'object-cloner.ideamix.es/kopf-finalizer'
    settings.persistence.diffbase_storage = kopf.StatusDiffBaseStorage(name='kopf-object-cloner')
    settings.persistence.progress_storage = kopf.StatusProgressStorage(field='status.kopf-object-cloner')
