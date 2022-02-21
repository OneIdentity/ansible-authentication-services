#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2021, One Identity LLC
# File: ad_group_conflicts_filters.py
# Desc: Ansible filters for ad_group_conflicts role
# Auth: Laszlo Nagy
# Note:
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# Future module imports for consistency across Python versions
from __future__ import absolute_import, division, print_function

# Want classes to be new type for consistency across Python versions
__metaclass__ = type

from ansible.errors import AnsibleFilterError


# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def select_conflicting_groups_by_schema(group_objects_list, group_gid_number_attr, group_name_attr):
    """
    Safeguard Authentication Services is designed to support any Active Directory schema
    configuration. If your Active Directory schema has built-in support for Unix attributes
    (Windows 2003 R2 schema, SFU schema), Safeguard Authentication Services automatically
    uses one of these schema configurations. Examples of group_object:
    {
        "DistinguishedName": "CN=AutoEnrollGroup,CN=Users,DC=QASDEV,DC=oi",
        "Name": "AutoEnrollGroup",
        "ObjectClass": "group",
        "ObjectGUID": "fe8d95e1-d620-4661-bc14-a7ae5b172956",
        "gidNumber": 641753664,
        "sAMAccountName": "AutoEnrollGroup"
    },
    {
        "DistinguishedName": "CN=TestGroup,CN=Users,DC=QASDEV,DC=oi",
        "Name": "TestGroup",
        "ObjectClass": "group",
        "ObjectGUID": "619b9645-8a92-4584-bb82-b4818be77e54",
        "gidNumber": 10001,
        "sAMAccountName": "TestGroup"
    },
    """

    attrs = ['DistinguishedName', group_name_attr, group_gid_number_attr]
    groups = []
    for group_object in group_objects_list:
        group = []
        for attr in attrs:
            if attr in group_object and group_object[attr]:
                group.append(group_object[attr])
            else:
                group.append('')
        # A Group object is considered to be 'Unix-enabled' if it has values for
        # the Group GID Number and Group Name.
        if group[1] and group[2]:
            groups.append(group)

    return select_conflicting_groups(groups)


def select_conflicting_groups_when_schemaless(group_objects_list):
    """
    If your Active Directory schema does not natively support Unix account attributes
    and a schema extension is not possible, Safeguard Authentication Services uses "schemaless"
    functionality where Unix account information is stored in the altSecurityIdentities attribute.
    Examples of group_object in schemaless mode:
    {
        "DistinguishedName": "CN=tg-1974,CN=Users,DC=d16,DC=sb",
        "Name": "tg-1974",
        "ObjectClass": "group",
        "ObjectGUID": "ee3b40d7-3419-45cc-8778-d90fd798ae2d",
        "altSecurityIdentities": [
            "X509:<S>CN=Posix Group<I>CN=Quest Software<DATA>GroupName: tg-1974",
            "X509:<S>CN=Posix Group<I>CN=Quest Software<DATA>GroupGidNumber: 8135"
        ]
    },
    {
        "DistinguishedName": "CN=tg-1993,CN=Users,DC=d16,DC=sb",
        "Name": "tg-1993",
        "ObjectClass": "group",
        "ObjectGUID": "1a7de3d9-d8ff-477b-8498-05ce330f9e11",
        "altSecurityIdentities": [
            "X509:<S>CN=Posix Group<I>CN=Quest Software<DATA>GroupName: tg-1993",
            "X509:<S>CN=Posix Group<I>CN=Quest Software<DATA>GroupGidNumber: 8136"
        ]
    }
    """

    attrs = ['GroupName', 'GroupGidNumber']
    groups = []
    for group_object in group_objects_list:
        group = []
        for attr in attrs:
            alt_sec_ids = group_object['altSecurityIdentities']
            for alt_sec_id in alt_sec_ids:
                label = 'X509:<S>CN=Posix Group<I>CN=Quest Software<DATA>' + attr + ':'
                if label in alt_sec_id:
                    group.append(alt_sec_id[len(label):].strip())
                    break
            else:
                group.append('')

        # A Group object is considered to be 'Unix-enabled' if it has values for
        # the Group GID Number and Group Name.
        if group[0] and group[1]:
            dn = 'DistinguishedName'
            if dn in group_object and group_object[dn]:
                group.insert(0, group_object[dn])
            else:
                group.insert(0, '')
            groups.append(group)

    return select_conflicting_groups(groups)


def select_conflicting_groups(groups):

    conflicting_groups = {}
    if len(groups) < 2:
        return conflicting_groups

    for id_outer, group_outer in enumerate(groups):
        for id_inner, group_inner in enumerate(groups):
            if id_inner <= id_outer:
                continue
            if group_outer[2] == group_inner[2]:
                group_gid_number = group_outer[2]
                if group_gid_number not in conflicting_groups:
                    conflicting_groups[group_gid_number] = []
                if group_outer not in conflicting_groups[group_gid_number]:
                    conflicting_groups[group_gid_number].append(group_outer)
                if group_inner not in conflicting_groups[group_gid_number]:
                    conflicting_groups[group_gid_number].append(group_inner)

    return conflicting_groups


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class FilterModule(object):
    """
    ad_group_conflicts role jinja2 filters
    """

    def filters(self):
        filters = {
            'conflictinggroupsbyschema': select_conflicting_groups_by_schema,
            'conflictinggroupswhenschemaless': select_conflicting_groups_when_schemaless
        }
        return filters
