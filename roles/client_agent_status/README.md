# `client_agent_status` Role

The `client_agent_status` role checks the health status of [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) agents.  Report generation can be enabled to provide CSV and HTML reports of the results.

## Requirements

The role requires the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software be installed on the client.  See [`client_sw`](../client_sw/README.md) role for how to peform client software installation using Ansible.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information. 

### Facts generation

Facts generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role facts generation variables](../common/README.md#facts-generation) in the [`common`](../common/README.md) role.

* `client_agent_status_facts_generate` enables facts generation.  Implicitely enabled if `client_agent_status_reports_generate` is set.

    Default value is: 
    ```yaml
    client_agent_status_facts_generate: "{{ facts_generate }}"
    ```

* `client_agent_status_facts_verbose` enables verbose facts generation which means that facts will also contain reported failures or warnings.

    Default value is: 
    ```yaml
    client_agent_status_facts_verbose: "{{ facts_verbose }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role report generation variables](../common/README.md#report-generation) in the [`common`](../common/README.md) role.

* `client_agent_status_reports_generate` enables report generation.  Reports are generated at the end of a `client_agent_status` run for all hosts.

    Default value is: 
    ```yaml
    client_agent_status_reports_generate: "{{ reports_generate }}"
    ```

  Disabling report generation if not needed will increase the speed of the `client_agent_status` role.

* `client_agent_status_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    client_agent_status_reports_backup: "{{ reports_backup }}"

    ```

* `client_agent_status_reports_details_format` sets the format of the details section in both the HTML and CSV reports.  Valid options:
    * `yaml` details will be in YAML format
    * `json` details will be in JSON format

    Default value is: 
    ```yaml
    client_agent_status_reports_details_format: "{{ reports_details_format }}"

    ```

* `client_agent_status_reports_host` sets the host on which the reports should be generated. 

    Default value is: 
    ```yaml
    client_agent_status_reports_host: "{{ reports_host }}"
    ```

* `client_agent_status_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `client_agent_status` role.

  Default value is:
    ```yaml
    client_join_reports: 
      - src:  client_agent_status_report.csv.j2   
        dest: client_agent_status_report.csv
      - src:  client_agent_status_report.html.j2
        dest: client_agent_status_report.html
    ```
  
  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `client_agent_status` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `client_agent_status_reports_host`.  If `client_agent_status_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Plugins

The `client_agent_status` role contains a plugin to support operation of the role:

* `vastool_status` module tests the machine's join against Active Directory and local configuration for various issues using the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) vastool binary status command.

## Usage

Below is a sample playbook using the `client_agent_status` role.

```yaml
---

- hosts: all
  gather_facts: false

  # The variables you would most likely want/need to override have been included
  vars:

    # Facts
    client_agent_status_facts_generate: true
    client_agent_status_facts_verbose: false

    # Reports
    client_agent_status_reports_generate: true
    client_agent_status_reports_backup: false

  roles:
    - name: oneidentity.authentication_services.client_agent_status
```

For a copy of this and other sample playbooks see [examples](../../examples/README.md)
