# `local_unix_groups` Role

The `local_unix_groups` role creates CSV and HTML reports that list all groups on all hosts or list the hosts where a specific group account exists in /etc/group.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information.

### Report parameters

To locate a specific group, use the following report parameters. When you specify multiple report parameters, it uses the AND expression; therefore, ALL of the selected parameters must be met in order to locate the group.

* `local_unix_groups_group_name`: Find groups where Group Name contains `local_unix_groups_group_name`.

    Default value is:
    ```yaml
    local_unix_groups_group_name: ''
    ```

* `local_unix_groups_gid_number`: Find groups where GID Number is `local_unix_groups_gid_number`.

    Default value is:
    ```yaml
    local_unix_groups_gid_number: ''
    ```

* `local_unix_groups_member`: Find groups where list of Members contains `local_unix_groups_member`.  The `local_unix_groups_member` accepts multiple entries separated by a comma.  Spaces are taken literally in the search.  For example, entering: 'adm, user' searches for members whose name contains 'adm' or ' user' while entering: 'adm,user' searches for members whose name contains 'adm' or 'user'.

    Default value is:
    ```yaml
    local_unix_groups_member: ''
    ```

* `local_unix_groups_include_all_group_members` includes all of the group members in the report.

    Default value is:
    ```yaml
    local_unix_groups_include_all_group_members: true
    ```

### Facts generation

Facts generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role facts generation variables](../common/README.md#facts-generation) in the [`common`](../common/README.md) role.

* `local_unix_groups_facts_generate` enables facts generation.  Implicitely enabled if `local_unix_groups_reports_generate` is set.

    Default value is:
    ```yaml
    local_unix_groups_facts_generate: "{{ facts_generate }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role report generation variables](../common/README.md#report-generation) in the [`common`](../common/README.md) role.

* `local_unix_groups_reports_generate` enables report generation.  Reports are generated at the end of a `local_unix_groups` run for all hosts.

    Default value is: 
    ```yaml
    local_unix_groups_reports_generate: "{{ reports_generate }}"
    ```

* `local_unix_groups_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    local_unix_groups_reports_backup: "{{ reports_backup }}"

    ```

* `local_unix_groups_reports_host` sets the host on which the reports should be generated.

    Default value is: 
    ```yaml
    local_unix_groups_reports_host: "{{ reports_host }}"
    ```

* `local_unix_groups_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `local_unix_groups` role.

  Default value is:
    ```yaml
    local_unix_groups_reports:
      - src:  local_unix_groups_report.csv.j2
        dest: local_unix_groups_report.csv
      - src:  local_unix_groups_report.html.j2
        dest: local_unix_groups_report.html
    ```

  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `local_unix_groups` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `local_unix_groups_reports_host`.  If `local_unix_groups_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Plugins

The `local_unix_groups` role contains a plugin to support operation of the role:

* `get_local_unix_groups` module reads, filters and returns data from /etc/group file.

## Usage

Below is a sample playbook using the `local_unix_groups` role.

```yaml
---

- hosts: all
  gather_facts: false

  # The variables you would most likely want/need to override have been included
  vars:

    # Report parameters
    local_unix_groups_group_name: ''
    local_unix_groups_gid_number: ''
    local_unix_groups_member: ''
    local_unix_groups_include_all_group_members: true

    # Facts
    local_unix_groups_facts_generate: true

    # Reports
    local_unix_groups_reports_generate: true
    local_unix_groups_reports_backup: false

  roles:
    - name: oneidentity.authentication_services.local_unix_groups
```

For a copy of this and other sample playbooks see [examples](../../examples/README.md)
