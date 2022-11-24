# Examples

A small collection of sample files has been included to help get you started.  The variables most likely to be overriden have been included in this playbook for your convenience even though many are still set to their default values.

# Inventory Examples

[Simple](inventory_simple.yml) and [complex](inventory_complex.yml) inventory files have been included.  There are many ways besides YAML files to pass inventory information to Ansible, see [Ansible documentation](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html) for further information.

# Role Examples

### `client_preflight` Role Example

The [`client_preflight`](run_client_preflight.yml) role example shows use of the `client_preflight` role in an Ansible playbook.

### `client_sw` Role Example

The [`client_sw`](run_client_sw.yml) role example shows use of the `client_sw` role in an Ansible playbook.

### `client_join` Role Example

The [`client_join`](run_client_join.yml) role example shows use of the `client_join` role in an Ansible playbook.

### `client_config` Role Example

The [`client_config`](run_client_config.yml) role example shows use of the `client_config` role in an Ansible playbook.

### `client_join_status` Role Example

The [`client_join_status`](run_client_join_status.yml) role example shows use of the `client_join_status` role in an Ansible playbook.

### `client_agent_status` Role Example

The [`client_agent_status`](run_client_agent_status.yml) role example shows use of the `client_agent_status` role in an Ansible playbook.

## Host reports

### `unix_computers_in_ad` Role Example

The [`unix_computers_in_ad`](run_unix_computers_in_ad.yml) role example shows use of the `unix_computers_in_ad` role in an Ansible playbook.

## User reports

### `ad_user_conflicts` Role Example

The [`ad_user_conflicts`](run_ad_user_conflicts.yml) role example shows use of the `ad_user_conflicts` role in an Ansible playbook.

### `local_unix_user_conflicts` Role Example

The [`local_unix_user_conflicts`](run_local_unix_user_conflicts.yml) role example shows use of the `local_unix_user_conflicts` role in an Ansible playbook.

### `local_unix_users` Role Example

The [`local_unix_users`](run_local_unix_users.yml) role example shows use of the `local_unix_users` role in an Ansible playbook.

### `local_unix_users_with_ad_logon` Role Example

The [`local_unix_users_with_ad_logon`](run_local_unix_users_with_ad_logon.yml) role example shows use of the `local_unix_users_with_ad_logon` role in an Ansible playbook.

### `unix_enabled_ad_users` Role Example

The [`unix_enabled_ad_users`](run_unix_enabled_ad_users.yml) role example shows use of the `unix_enabled_ad_users` role in an Ansible playbook.

## Group reports

### `ad_group_conflicts` Role Example

The [`ad_group_conflicts`](run_ad_group_conflicts.yml) role example shows use of the `ad_group_conflicts` role in an Ansible playbook.

### `local_unix_groups` Role Example

The [`local_unix_groups`](run_local_unix_groups.yml) role example shows use of the `local_unix_groups` role in an Ansible playbook.

### `unix_enabled_ad_groups` Role Example

The [`unix_enabled_ad_groups`](run_unix_enabled_ad_groups.yml) role example shows use of the `unix_enabled_ad_groups` role in an Ansible playbook.

## Access & Privileges reports

### `logon_policy_for_unix_host` Role Example

The [`logon_policy_for_unix_host`](run_logon_policy_for_unix_host.yml) role example shows use of the `logon_policy_for_unix_host` role in an Ansible playbook.

### `logon_policy_for_ad_user` Role Example

The [`logon_policy_for_ad_user`](run_logon_policy_for_ad_user.yml) role example shows use of the `logon_policy_for_ad_user` role in an Ansible playbook.

### `host_access_control` Role Example

The [`host_access_control`](run_host_access_control.yml) role example shows use of the `host_access_control` role in an Ansible playbook.

