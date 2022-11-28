#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2022, One Identity LLC
# File: get_join_status.py
# Desc: Ansible module that checks if client is joined to AD.
# Auth: Laszlo Nagy
# Note:
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Required Ansible documentation
# ------------------------------------------------------------------------------

ANSIBLE_METADATA = {
    'metadata_version': '0.2',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: get_join_status

short_description: Checks Active Directory join status

version_added: '2.9'

description: >
    Checks Active Directory join status using the Authentication Services vastool binary.

options:
    facts_key:
        description:
            - Ansible facts key
        type: str
        required: false
        default: 'get_join_status'

author:
    - Laszlo Nagy (laszlo.nagy@oneidentity.com)
"""

EXAMPLES = """
- name: Normal usage
  check_join_state:
    facts_key: sas_client_join_state
  register: check_join_state_result
"""

RETURN = """
ansible_facts:
    description: All non-standard return values are placed in Ansible facts
    type: dict
    returned: always
    keys:
        changed:
            description: Did the state of the host change?
            type: bool
            returned: always
        failed:
            description: Did the module fail?
            type: bool
            returned: always
        msg:
            description: Additional information if failed
            type: str
            returned: always
        params:
            description: Parameters passed in
            type: dict
            returned: always
        version:
            description: Version of SAS
            type: str
            returned: always
        domain:
            description: Active Directory domain client is joined
            type: str
            returned: always
"""


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from ansible.module_utils.basic import AnsibleModule
import traceback
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.vastool as vt
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.check_file_exec as cfe


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Defaults
FACTS_KEY_DEFAULT = 'get_join_status'


# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def run_module():
    """
    Main Ansible module function
    """

    # Module argument info
    module_args = {
            'facts_key': {
                'type': 'str',
                'required': False,
                'default': FACTS_KEY_DEFAULT
            }
        }

    # Seed result value
    result = {
            'changed': False,
            'failed': False,
            'msg': ''
        }

    # Lean on boilerplate code in AnsibleModule class
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # Run logic
    # NOTE: This module does not support check mode right now so no special check handling
    err, result = run_normal(module.params, result)

    # Exit
    module.exit_json(**result)


# ------------------------------------------------------------------------------
def run_normal(params, result):
    """
    Normal mode logic.

    params contains input parameters.

    result contains run results skeleton, will modify/add to and then return
    this value along with an err value that contains None if no error or a string
    describing the error.
    """

    # Return data
    err = None
    version = ''
    changed = False
    version = ''
    domain = ''

    # Parameters
    facts_key = params['facts_key'] if params['facts_key'] else FACTS_KEY_DEFAULT

    try:

        err, version = cfe.check_file_exec(vt.VASTOOL_PATH, '-v')
        if err is None:
            domain = vt.vastool_status()

    except Exception:
        tb = traceback.format_exc()
        err = str(tb)

    # Build result
    result['changed'] = changed
    result['failed'] = err is not None
    result['msg'] = err if err is not None else ''

    # Create ansible_facts data
    result_facts = result.copy()
    result_facts['params'] = params
    result_facts['version'] = version
    result_facts['domain'] = domain
    result['ansible_facts'] = {facts_key: result_facts}

    # Return
    return err, result


# ------------------------------------------------------------------------------
def main():
    """
    Main
    """

    run_module()


# When run from command line
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
