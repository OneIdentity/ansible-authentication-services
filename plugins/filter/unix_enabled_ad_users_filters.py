#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2021, One Identity LLC
# File: unix_enabled_ad_users_filters.py
# Desc: Ansible filters for unix_enabled_ad_users role
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
def extract_properties_by_schema(user_objects_list, uid_number_attr, login_name_attr,
    primary_gid_number_attr, gecos_attr, home_directory_attr, login_shell_attr):
    """
    Safeguard Authentication Services is designed to support any Active Directory schema
    configuration. If your Active Directory schema has built-in support for Unix attributes
    (Windows 2003 R2 schema, SFU schema), Safeguard Authentication Services automatically
    uses one of these schema configurations. Examples of user_object:
    {
        "DistinguishedName": "CN=fuser,CN=Users,DC=QASDEV,DC=oi",
        "Name": "fuser",
        "ObjectClass": "user",
        "ObjectGUID": "b89305e3-76a9-48f7-8121-268d5d8ceeca",
        "gecos": ",,,",
        "gidNumber": 1001,
        "loginShell": "/bin/bash",
        "sAMAccountName": "fuser",
        "uidNumber": 1002,
        "unixHomeDirectory": "/home/fuser"
    },
    {
        "DistinguishedName": "CN=eripley,CN=Users,DC=QASDEV,DC=oi",
        "Name": "eripley",
        "ObjectClass": "user",
        "ObjectGUID": "76dc716d-f130-4d70-849b-3443f4b3daa1",
        "gecos": "Ellen Ripley",
        "gidNumber": 10001,
        "loginShell": "/bin/bash",
        "sAMAccountName": "eripley",
        "uidNumber": 1003,
        "unixHomeDirectory": "/home/eripley"
    }
    """

    attrs = ['DistinguishedName', login_name_attr, uid_number_attr,
        primary_gid_number_attr, gecos_attr, home_directory_attr, login_shell_attr]
    users = []
    for user_object in user_objects_list:
        user = []
        for attr in attrs:
            if attr in user_object and user_object[attr]:
                user.append(user_object[attr])
            else:
                user.append('')
        # A User object is considered to be 'Unix-enabled' if it has values for
        # the UID Number, Primary GID Number, Home Directory and Login Shell.
        # If Login Shell is /bin/false, the user is considered to be disabled
        # for Unix or Linux logon.
        if user[2] and user[3] and user[5] and user[6] and user[6] != '/bin/false':
            users.append(user)

    return users


def extract_properties_when_schemaless(user_objects_list):
    """
    If your Active Directory schema does not natively support Unix account attributes
    and a schema extension is not possible, Safeguard Authentication Services uses "schemaless"
    functionality where Unix account information is stored in the altSecurityIdentities attribute.
    Examples of user_object in schemaless mode:
    {
        "DistinguishedName": "CN=tu4sp4-d16,OU=SPUG4,OU=SPUG3,OU=SPUG,DC=d16,DC=sb",
        "Name": "tu4sp4-d16",
        "ObjectClass": "user",
        "ObjectGUID": "87e2e7c7-603d-4fe9-92e6-e0b8f0327a82",
        "altSecurityIdentities": [
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>LoginShell: /bin/sh",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>HomeDirectory: /home/tu4sp4-d16",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>Gecos: tu4sp4-d16",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>UserGidNumber: 8000",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>LoginName: tu4sp4-d16",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>UidNumber: 1480909686"
        ]
    },
    {
        "DistinguishedName": "CN=ssu,OU=smoke,DC=d16,DC=sb",
        "Name": "ssu",
        "ObjectClass": "user",
        "ObjectGUID": "9946c640-3982-4f5a-8795-5db95ffc861b",
        "altSecurityIdentities": [
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>UserGidNumber:1593431050",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>UidNumber:446089076",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>LoginShell:/bin/sh",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>LoginName:ssu",
            "X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>HomeDirectory:/home/ssu"
        ]
    }
    """

    attrs = ['LoginName', 'UidNumber',
        'UserGidNumber', 'Gecos', 'HomeDirectory', 'LoginShell']
    users = []
    for user_object in user_objects_list:
        user = []
        for attr in attrs:
            alt_sec_ids = user_object['altSecurityIdentities']
            for alt_sec_id in alt_sec_ids:
                label = 'X509:<S>CN=Posix Account<I>CN=Quest Software<DATA>' + attr + ':'
                if label in alt_sec_id:
                    user.append(alt_sec_id[len(label):].strip())
                    break
            else:
                user.append('')

        # A User object is considered to be 'Unix-enabled' if it has values for
        # the UID Number, Primary GID Number, Home Directory and Login Shell.
        # If Login Shell is /bin/false, the user is considered to be disabled
        # for Unix or Linux logon.
        if user[1] and user[2] and user[4] and user[5] and user[5] != '/bin/false':
            dn = 'DistinguishedName'
            if dn in user_object and user_object[dn]:
                user.insert(0, user_object[dn])
            else:
                user.insert(0, '')
            users.append(user)

    return users


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class FilterModule(object):
    """
    unix_enabled_ad_users role jinja2 filters
    """

    def filters(self):
        filters = {
            'usersbyschema': extract_properties_by_schema,
            'userswhenschemaless': extract_properties_when_schemaless
        }
        return filters
