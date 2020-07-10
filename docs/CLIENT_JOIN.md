# `client_join` Role

The `client_join` role performs [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client Active Directory joins and unjoins.  Report generation can be enabled to provide CSV and HTML reports of the results.

## Requirements

The role requires the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software be installed on the client.  See [`client_sw role`](docs/CLIENT_SW.md) for how to peform client software installation using Ansible.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information. 

### Active Directory

See [Active Directory variables](./COMMON.md##ActiveDirectory) in `common role`.

* `client_join_state` sets the desired join state.  Possible state values:

    * `joined` joined to specified Active Directory domain. 
    * `unjoined` unjoined from specified Active Directory domain.

    Default value is: 
    ```yaml
    client_join_state: joined
    ```

### Vastool Binary

* `client_join_extra_args` allows passing additional arguments to the vastool binary.  `client_join` uses the `join` and `unjoin` vastool commands.

    Default value is: 
    ```yaml
    client_preflight_extra_args:
    ```

### Facts generation

Facts generation variable defaults for all roles are set by variables in the `common role` and can be overriden for all roles by setting the appropriate `common role` variable.  See [common role facts generation variables](./COMMON.md##FactsGeneration) in `common role`.

* `client_join_facts_generate` enables facts generation.  Implicitely enabled if `client_join_reports_generate` is set.

    Default value is: 
    ```yaml
    client_join_facts_generate: "{{ facts_generate }}"
    ```

* `client_join_facts_verbose` enables verbose facts generation.

    Default value is: 
    ```yaml
    client_join_facts_verbose: "{{ facts_verbose }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the `common role` and can be overriden for all roles by setting the appropriate `common role` variable.  See [common role reports generation variables](./COMMON.md##ReportsGeneration) in `common role`.

* `client_join_reports_generate` enables report generation.  Reports are generated at the end of a `client_join` run for all hosts.

    Default value is: 
    ```yaml
    client_join_reports_generate: "{{ reports_generate }}"
    ```

  Disabling report generation if not needed will increase the speed of the `client_join` role.

* `client_join_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    client_join_reports_backup: "{{ reports_backup }}"

    ```

* `client_join_reports_details_format` sets the format of the details section in both the HTML and CSV reports.  Valid options:
    * `yaml` details will be in YAML format
    * `json` details will be in JSON format

    Default value is: 
    ```yaml
    client_join_reports_details_format: "{{ reports_details_format }}"

    ```

* `client_join_reports_host` sets the host on which the reports should be generated. 

    Default value is: 
    ```yaml
    client_join_reports_host: "{{ reports_host }}"
    ```

* `client_join_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `client_join` role.

  Default value is:
    ```yaml
    client_join_reports: 
      - src:  client_join_report.csv.j2   
        dest: client_join_report.csv
      - src:  client_join_report.html.j2
        dest: client_join_report.html
    ```
  
  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `client_join` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `client_join_reports_host`.  If `client_join_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Plugins

The `client_join` role contains a plugin to support operation of the role:

* `vastool_join` module performs Active Directory join/unjoin tasks on host by wrapping the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) vastool binary join and unjoin commands.

## Usage

Below is a sample playbook using the `client_join` role.

```yaml
---

- hosts: all 
  gather_facts: false

  # The variables you would most likely want/need to override have been included
  vars:

    # Active Directory
    client_join_state: joined
    client_domain: sample.net
    client_username: user
    client_password: pass

    # Facts
    client_join_facts_generate: true
    client_join_facts_verbose: false

    # Reports
    client_join_reports_generate: true 
    client_join_reports_backup: false 

  roles:
    - name: oneidentity.authentication_services.client_join
```

See sample [HTML](client_join_report.html) and [CSV](client_join_report.csv) reports generated from a run of this sample playbook.

For a copy of this and other sample playbooks see [examples](../examples/README.md)
