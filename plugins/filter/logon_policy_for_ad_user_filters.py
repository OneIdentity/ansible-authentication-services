#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2022, One Identity LLC
# File: logon_policy_for_ad_user_filters.py
# Desc: Ansible filters for logon_policy_for_ad_user role
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
def get_logon_policy_for_ad_user(logon_policy_for_unix_hosts):
    """
    Example of logon_policy_for_unix_hosts:
    {
        "192.168.56.101": [
            [
                "QASDEV\\eripley",
                "VAS",
                "1003",
                "10001",
                "Ellen Ripley",
                "/home/eripley",
                "/bin/bash"
            ],
            [
                "QASDEV\\smartbela",
                "VAS",
                "1371126438",
                "1000",
                "Bela Smart",
                "/home/smartbela",
                "/bin/bash"
            ]
        ],
        "192.168.56.103": [
            [
                "QASDEV\\eripley",
                "VAS",
                "1003",
                "10001",
                "Ellen Ripley",
                "/home/eripley",
                "/bin/bash"
            ],
            [
                "QASDEV\\senior",
                "VAS",
                "1234567",
                "1000",
                "Senior",
                "/home/Senior",
                "/bin/bash"
            ]
        ]
    }
    """

    users = {}
    for host in logon_policy_for_unix_hosts:
        users_allowed = logon_policy_for_unix_hosts[host]
        for user in users_allowed:
            if user[0] not in users:
                users.update({user[0]: {'user': user, 'hosts': [host]} })
            else:
                users[user[0]]['hosts'].append(host)

    return users


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class FilterModule(object):
    """
    logon_policy_for_ad_user role jinja2 filters
    """

    def filters(self):
        filters = {
            'logonpolicyforaduser': get_logon_policy_for_ad_user
        }
        return filters
