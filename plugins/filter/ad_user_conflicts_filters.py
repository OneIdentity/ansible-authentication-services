#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2021, One Identity LLC
# File: ad_user_conflicts_filters.py
# Desc: Ansible filters for ad_user_conflicts role
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
def select_conflicting_users(user_objects_list, uid_attr, shell_attr):
    """
    Safeguard Authentication Services is designed to support any Active Directory schema
    configuration. If your Active Directory schema has built-in support for Unix attributes
    (Windows 2003 R2 schema, SFU schema), Safeguard Authentication Services automatically
    uses one of these schema configurations. Example of user_object:
    {
        "DistinguishedName": "CN=Aba Samuel,CN=Users,DC=QASDEV,DC=oi",
        "sAMAccountName": "abasamuel",
        "uidNumber": 1995995320,
        "loginShell": "/bin/sh"
    }

    However, if your Active Directory schema does not natively support Unix account attributes
    and a schema extension is not possible, Safeguard Authentication Services uses "schemaless"
    functionality where Unix account information is stored in the altSecurityIdentities attribute.
    Example of user_object in schemaless mode:
    {
        "DistinguishedName": "CN=TestUser 2011,CN=Users,DC=d16,DC=sb",
        "altSecurityIdentities": [
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>LoginShell: /bin/sh",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>HomeDirectory: /home/TestUser 2011",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>Gecos: TestUser 2011",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>UserGidNumber: 8000",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>LoginName: TestUser 2011",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>UidNumber: 8085"
        ],
        "sAMAccountName": "tu-2011-sam"
    }
    """

    # Make sure user_objects_list is a list
    if not isinstance(user_objects_list, list):
        raise AnsibleFilterError("selectconflictingusers requires a list, got %s instead." % type(user_objects_list))

    conflicting_users = {}
    if len(user_objects_list) < 2:
        return conflicting_users

    users = []
    if 'altSecurityIdentities' in user_objects_list[0]:
        uid_label = 'X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>UidNumber:'
        shell_label = 'X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>LoginShell:'
        for user_object in user_objects_list:
            attr_list = user_object['altSecurityIdentities']
            unix_enabled = True
            for attr in attr_list:
                if shell_label in attr:
                    shell = attr[ len(shell_label) : ].strip()
                    if shell == '/bin/false':
                        unix_enabled = False
                    break
            if unix_enabled:
                for attr in attr_list:
                    if uid_label in attr:
                        users.append({
                            'uidNumber': attr[ len(uid_label) : ].strip(),
                            'DistinguishedName': user_object['DistinguishedName'],
                            'sAMAccountName': user_object['sAMAccountName']})
                        break
    elif uid_attr in user_objects_list[0]:
        for user_object in user_objects_list:
            if user_object[shell_attr] != '/bin/false':
                users.append({
                    'uidNumber': user_object[uid_attr],
                    'DistinguishedName': user_object['DistinguishedName'],
                    'sAMAccountName': user_object['sAMAccountName']})

    for id_outer, user_outer in enumerate(users):
        for id_inner, user_inner in enumerate(users):
            if id_inner <= id_outer:
                continue
            if user_outer['uidNumber'] == user_inner['uidNumber']:
                uid_number = user_outer['uidNumber']
                if uid_number not in conflicting_users:
                    conflicting_users[uid_number] = []
                if user_outer not in conflicting_users[uid_number]:
                    conflicting_users[uid_number].append(user_outer)
                if user_inner not in conflicting_users[uid_number]:
                    conflicting_users[uid_number].append(user_inner)

    return conflicting_users


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class FilterModule(object):
    """
    ad_user_conflicts role jinja2 filters
    """

    def filters(self):
        filters = {
            'selectconflictingusers': select_conflicting_users,
        }
        return filters
