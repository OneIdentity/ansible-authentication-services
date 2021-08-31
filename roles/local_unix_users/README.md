# `local_unix_users` Role

The `local_unix_users` role creates CSV and HTML reports that list all users on all hosts or list the hosts where a specific user account exists in /etc/passwd.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information.

### Report parameters

To locate a specific user, use the following report parameters. When you specify multiple report parameters, it uses the AND expression; therefore, ALL of the selected parameters must be met in order to locate the user account.

* `local_unix_users_user_name`: Find users where User Name contains `local_unix_users_user_name`.

    Default value is:
    ```yaml
    local_unix_users_user_name: ''
    ```

* `local_unix_users_uid_number`: Find users where UID Number is `local_unix_users_uid_number`.

    Default value is:
    ```yaml
    local_unix_users_uid_number: ''
    ```

* `local_unix_users_primary_gid_number`: Find users where Primary GID Number is `local_unix_users_primary_gid_number`.

    Default value is:
    ```yaml
    local_unix_users_primary_gid_number: ''
    ```

* `local_unix_users_comment`: Find users where Comment (GECOS) contains `local_unix_users_comment`.

    Default value is:
    ```yaml
    local_unix_users_comment: ''
    ```

* `local_unix_users_home_directory`: Find users where Home Directory contains `local_unix_users_home_directory`.

    Default value is:
    ```yaml
    local_unix_users_home_directory: ''
    ```

* `local_unix_users_login_shell`: Find users where Login Shell contains `local_unix_users_login_shell`.

    Default value is:
    ```yaml
    local_unix_users_login_shell: ''
    ```

### Facts generation

Facts generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role facts generation variables](../common/README.md#facts-generation) in the [`common`](../common/README.md) role.

* `local_unix_users_facts_generate` enables facts generation.  Implicitely enabled if `local_unix_users_reports_generate` is set.

    Default value is:
    ```yaml
    local_unix_users_facts_generate: "{{ facts_generate }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role report generation variables](../common/README.md#report-generation) in the [`common`](../common/README.md) role.

* `local_unix_users_reports_generate` enables report generation.  Reports are generated at the end of a `local_unix_users` run for all hosts.

    Default value is: 
    ```yaml
    local_unix_users_reports_generate: "{{ reports_generate }}"
    ```

* `local_unix_users_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    local_unix_users_reports_backup: "{{ reports_backup }}"

    ```

* `local_unix_users_reports_host` sets the host on which the reports should be generated.

    Default value is: 
    ```yaml
    local_unix_users_reports_host: "{{ reports_host }}"
    ```

* `local_unix_users_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `local_unix_users` role.

  Default value is:
    ```yaml
    local_unix_users_reports:
      - src:  local_unix_users_report.csv.j2
        dest: local_unix_users_report.csv
      - src:  local_unix_users_report.html.j2
        dest: local_unix_users_report.html
    ```

  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `local_unix_users` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `local_unix_users_reports_host`.  If `local_unix_users_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Plugins

The `local_unix_users` role contains a plugin to support operation of the role:

* `get_local_unix_users` module reads, filters and returns data from /etc/passwd file.

## Usage

Below is a sample playbook using the `local_unix_users` role.

```yaml
---

- hosts: all
  gather_facts: false

  # The variables you would most likely want/need to override have been included
  vars:

    # Report parameters
    local_unix_users_user_name: ''
    local_unix_users_uid_number: ''
    local_unix_users_primary_gid_number: ''
    local_unix_users_comment: ''
    local_unix_users_home_directory: ''
    local_unix_users_login_shell: ''

    # Facts
    local_unix_users_facts_generate: true

    # Reports
    local_unix_users_reports_generate: true
    local_unix_users_reports_backup: false

  roles:
    - name: oneidentity.authentication_services.local_unix_users
```

For a copy of this and other sample playbooks see [examples](../../examples/README.md)
