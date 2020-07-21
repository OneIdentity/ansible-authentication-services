#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2020, One Identity LLC
# File: client_sw_filters.py
# Desc: Ansible filters for client_sw role
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
def pkg_items_append(pkg_items, pkg_dict, pkg_state, vasclnt_order):
    """
    Append packages from pkg_dict to pkg_items if their state matches pkg_state.

    vasclnt order can be 'first', 'last', or None which controls the order in
    which vasclnt is added to the list.  'first' and 'last' are self-
    explanatory and None adds vasclnt in alphabetical order like the rest of the
    packages.

    pkg_items is a list of package dicts with 'key' and 'value' keys for the
    package name and state.  This is a format Ansible expects for an item
    list (Ansible loop control statement.)
    """

    vasclnt_pkgs = ['vasclnt', 'vasclnts']

    # vasclnt first
    if vasclnt_order == 'first':
        for pkg in vasclnt_pkgs:
            pkg_item_append(pkg_items, pkg_dict, pkg, pkg_state)

    # Add all packages including vasclnt if order is None
    # Make a copy of pkt_dict to iterate because we may modify pkg_dict during iteration
    pkg_dict_temp = pkg_dict.copy()
    for pkg in sorted(pkg_dict_temp):
        if vasclnt_order is None or pkg not in vasclnt_pkgs:
            pkg_item_append(pkg_items, pkg_dict, pkg, pkg_state)

    # vasclnt last
    if vasclnt_order == 'last':
        for pkg in vasclnt_pkgs:
            pkg_item_append(pkg_items, pkg_dict, pkg, pkg_state)


# ------------------------------------------------------------------------------
def pkg_item_append(pkg_items, pkg_dict, pkg_name, pkg_state):
    """
    Append package from pkg_dict to pkg_items and remove it from pkg_dict if its
    name matches pkg_name and its state matches pkg_state.  Note that a
    pkg_state of None will match any state.

    pkg_items is a list of package dicts with 'key' and 'value' keys for the
    package name and state.  This is a format Ansible expects for an item
    list (Ansible loop control statement.)
    """

    if pkg_name in pkg_dict:
        if pkg_dict[pkg_name] == pkg_state or pkg_state is None:
            pkg_items.append({'key': pkg_name, 'value': pkg_dict[pkg_name]})
            del pkg_dict[pkg_name]


# ------------------------------------------------------------------------------
def pkg_dict_2_items(pkg_dict):
    """
    Transforms a dictionary of package (pkg_dict) to a item list of packages
    ordered by package state and name.

    Absent packages are ordered first with vasclnt(s) always coming last and all
    other packages in alphabetical order.

    Present packages are ordered next with vasclnt(s) always coming first and all
    other packages in alphabetical order.

    Check packages are ordered next in alphabetical order.

    Packages with an unexpected state value are ordered last in alphabetical
    order.
    """

    # Make sure pkg_dict is a dictionary
    if not isinstance(pkg_dict, Mapping):
        raise AnsibleFilterError("pkgdict2items requires a dictionary, got %s instead." % type(pkg_dict))

    # List of tuples containing package state and vasclnt order
    pkg_states = [
        ('absent', 'last'),
        ('present', 'first'),
        ('check', None),
        (None, None)
    ]

    # Build package items list
    pkg_items = []
    for pkg_state, vasclnt_order in pkg_states:
        pkg_items_append(pkg_items, pkg_dict, pkg_state, vasclnt_order)

    # Return list of package items ready for Ansible iteration
    return pkg_items


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class FilterModule(object):
    """
    client_sw role jinja2 filters
    """

    def filters(self):
        filters = {
            'pkgdict2items': pkg_dict_2_items,
        }
        return filters
