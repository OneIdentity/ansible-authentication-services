#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2020, One Identity LLC
# File: client_config_filters.py
# Desc: Ansible filters for client_config role
# Auth: Mark Stillings
# Note: 
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# Future module imports for consistency across Python versions
from __future__ import absolute_import, division, print_function

# Want classes to be new type for consistency across Python versions
__metaclass__ = type

from ansible.module_utils.common._collections_compat import Mapping
from ansible.errors import AnsibleFilterError


# ------------------------------------------------------------------------------
# Helper functions 
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def dict_list_select(dict_list, keys, default_value='', include_conditions={}, exclude_conditions={}):
    """ 
    Transforms a list of dictionaries into a new list of dictionaries that only
    includes the specified keys.  List entries that are missing key(s) will
    get the default value assigned.
    """ 

    # Make sure dict_list is a list
    if not isinstance(dict_list, list):
        raise AnsibleFilterError("dictlistfilter requires a list, got %s instead." % type(dict_list))

    # Make sure include_conditions is a mapping
    if not isinstance(include_conditions, Mapping):
        raise AnsibleFilterError("dictlistfilter requires include_conditions to be a mapping, got %s instead." % type(include_conditions))
        
    # Make sure include_conditions is a mapping
    if not isinstance(exclude_conditions, Mapping):
        raise AnsibleFilterError("dictlistfilter requires exclude_conditions to be a mapping, got %s instead." % type(exclude_conditions))

    # If keys not a list then make it a list
    if not isinstance(keys, list):
        keys = list(keys)

    # Build package items list
    dict_list_s = []
    for d in dict_list:

        d_s = {}
        included = len(include_conditions) == 0
        excluded = False
        for key in keys:
            d_s[key] = d[key] if key in d else default_value

            # Check for inclusion 
            if key in include_conditions and d_s[key] == include_conditions[key]:
                included = True
            
            # Check for exclusion 
            if key in exclude_conditions and d_s[key] == exclude_conditions[key]:
                excluded = True

        if included and not excluded:
            dict_list_s += [d_s]

    # Return list of package items ready for Ansible iteration
    return dict_list_s


# ------------------------------------------------------------------------------
# Classes 
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class FilterModule(object):
    """
    client_config role jinja2 filters
    """

    def filters(self):
        filters = {
            'dictlistselect': dict_list_select,
        }
        return filters
