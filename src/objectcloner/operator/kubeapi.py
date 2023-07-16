"""Provides decorator that inject Kubernetes API object."""
import os
import pykube


def kubernetes_api(function):
    """
    Injects a Kubernetes API into a wrapped function.

    :param function: A function that requires access to Kubernetes API
    :return:
    """
    def wrap_function(*args, **kwargs):
        api = _get_kube_api()
        res = function(api, *args, **kwargs)
        api.session.close()
        return res
    return wrap_function


def _get_kube_api():
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        config = pykube.KubeConfig.from_file(os.getenv("KUBECONFIG", "~/.kube/config"))
    api = pykube.HTTPClient(config, verify=False)
    return api
