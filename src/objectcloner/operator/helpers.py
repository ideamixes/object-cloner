"""Contains only a function that allows to remove nested keys from a dict"""
import re


def delete_fields(obj, field_paths, **_):
    """
    Deleted nested fields specified a list of field names from a dict.

    :param obj:
    :param field_paths:
    :param _:
    :return:
    """
    for field_path in field_paths:
        _delete_field(obj, field_path.copy())


def _delete_field(obj, field_path):
    """
    Recursively process each field starting from the first level. Evaluates each field if it should be deleted.

    :param obj:
    :param field_path:
    :return:
    """
    field_regex = field_path.pop(0)
    is_last_level = len(field_path) == 0
    are_one_or_more_level_fields_deleted = False
    for key in list(obj.keys()).copy():
        if re.match(field_regex, key):
            if is_last_level:
                del obj[key]
                are_one_or_more_level_fields_deleted = True
            else:
                if isinstance(obj[key], dict):
                    is_child_field_deleted = _delete_field(obj[key], field_path)
                    if is_child_field_deleted and len(obj[key]) == 0:
                        del obj[key]
                        are_one_or_more_level_fields_deleted = True
    return are_one_or_more_level_fields_deleted
