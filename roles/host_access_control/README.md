# `host_access_control` Role

The `host_access_control` role creates CSV and HTML reports that show the content of users.allow and users.deny files.  In [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) file-based access control involves checking access control rules stored locally on each workstation in users.allow and users.deny.

## Requirements

The role requires the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software be installed on the client.  See [`client_sw`](../client_sw/README.md) role for how to peform client software installation using Ansible.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information.

### Facts generation

Facts generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role facts generation variables](../common/README.md#facts-generation) in the [`common`](../common/README.md) role.

* `host_access_control_facts_generate` enables facts generation.  Implicitely enabled if `host_access_control_reports_generate` is set.

    Default value is: 
    ```yaml
    host_access_control_facts_generate: "{{ facts_generate }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role report generation variables](../common/README.md#report-generation) in the [`common`](../common/README.md) role.

* `host_access_control_reports_generate` enables report generation.  Reports are generated at the end of a `host_access_control` run for all hosts.

    Default value is: 
    ```yaml
    host_access_control_reports_generate: "{{ reports_generate }}"
    ```

* `host_access_control_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    host_access_control_reports_backup: "{{ reports_backup }}"

    ```

* `host_access_control_reports_details_format` sets the format of the details section in both the HTML and CSV reports.  Valid options:
    * `yaml` details will be in YAML format
    * `json` details will be in JSON format

    Default value is: 
    ```yaml
    host_access_control_reports_details_format: "{{ reports_details_format }}"

    ```

* `host_access_control_reports_host` sets the host on which the reports should be generated.

    Default value is: 
    ```yaml
    host_access_control_reports_host: "{{ reports_host }}"
    ```

* `host_access_control_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `host_access_control` role.

  Default value is:
    ```yaml
    host_access_control_reports: 
      - src:  host_access_control_report.csv.j2
        dest: host_access_control_report.csv
      - src:  host_access_control_report.html.j2
        dest: host_access_control_report.html
    ```

  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `host_access_control` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `host_access_control_reports_host`.  If `host_access_control_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Plugins

The `host_access_control` role contains a plugin to support operation of the role:

* `get_host_access_control` module returns list of Active Directory users, groups, organizational units and domain names from users.allow and users.deny.

## Usage

Below is a sample playbook using the `host_access_control` role.

```yaml
---

- hosts: all
  gather_facts: false

  # The variables you would most likely want/need to override have been included
  vars:

    # Facts
    host_access_control_facts_generate: true

    # Reports
    host_access_control_reports_generate: true
    host_access_control_reports_backup: false

  roles:
    - name: oneidentity.authentication_services.host_access_control
```

For a copy of this and other sample playbooks see [examples](../../examples/README.md)
