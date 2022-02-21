# `unix_enabled_ad_users` Role

The `unix_enabled_ad_users` role creates CSV and HTML reports that lists all Active Directory users that have Unix user attributes.  A User object is considered to be 'Unix-enabled' if it has values for the UID Number, Primary GID Number, Home Directory and Login Shell.  If Login Shell is /bin/false, the user is considered to be disabled for Unix or Linux logon.

## Requirements

The role requires the `community.windows` collection be installed on the control node (the machine that runs Ansible).  See [community.windows](https://galaxy.ansible.com/community/windows) for how to perform installation.

The role gathers information about Active Directory objects.  For Ansible to communicate to a Windows host and use Windows modules, the Windows host must meet some requirements.  See [Connecting to a Windows Host](https://www.ansible.com/blog/connecting-to-a-windows-host) for guidance.  See [Setting up a Windows Host](https://docs.ansible.com/ansible/latest/user_guide/windows_setup.html) and [Windows Remote Management](https://docs.ansible.com/ansible/latest/user_guide/windows_winrm.html) for further details.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information.

### Active Directory

See [Active Directory variables](../common/README.md#active-directory) in the [`common`](../common/README.md) role.

### Report parameters

* `unix_enabled_ad_users_base_container`: By default, these reports are created using the default domain as the base container.  With this parameter you can specify a different base container to begin the search.

    Default value is:
    ```yaml
    unix_enabled_ad_users_base_container: ''
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role report generation variables](../common/README.md#report-generation) in the [`common`](../common/README.md) role.

* `unix_enabled_ad_users_reports_generate` enables report generation.

    Default value is:
    ```yaml
    unix_enabled_ad_users_reports_generate: "{{ reports_generate }}"
    ```

* `unix_enabled_ad_users_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is:
    ```yaml
    unix_enabled_ad_users_reports_backup: "{{ reports_backup }}"

    ```

* `unix_enabled_ad_users_reports_host` sets the host on which the reports should be generated.

    Default value is: 
    ```yaml
    unix_enabled_ad_users_reports_host: "{{ reports_host }}"
    ```

* `unix_enabled_ad_users_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `unix_enabled_ad_users` role.

  Default value is:
    ```yaml
    unix_enabled_ad_users_reports:
      - src:  unix_enabled_ad_users_report.csv.j2
        dest: unix_enabled_ad_users_report.csv
      - src:  unix_enabled_ad_users_report.html.j2
        dest: unix_enabled_ad_users_report.html
    ```

  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `unix_enabled_ad_users` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `unix_enabled_ad_users_reports_host`.  If `unix_enabled_ad_users_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Usage

Below is a sample playbook using the `unix_enabled_ad_users` role.

```yaml
---

- hosts: all
  gather_facts: false

  # The variables you would most likely want/need to override have been included
  vars:

    # Active Directory
    client_domain: sample.net
    client_username: user
    client_password: pass

    # Report parameters
    unix_enabled_ad_users_base_container: 'CN=Users,DC=Sample,DC=net'

    # Reports
    unix_enabled_ad_users_reports_generate: true
    unix_enabled_ad_users_reports_backup: false

  roles:
    - name: oneidentity.authentication_services.unix_enabled_ad_users
```

For a copy of this and other sample playbooks see [examples](../../examples/README.md)
