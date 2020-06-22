# `client_preflight` Role

The `client_preflight` role checks client readiness for [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software installation and Active Directory joining.  Report generation can be enabled to provide CSV and HTML reports of the results.

## Requirements

The role requires the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software install packages be available on Ansible control node.  See [variables](##Variables) section for more detail.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information. 

### Client Software Directories

See [client software directories variables](./COMMON.md##ClientSoftwareDirectories) in `common role`.

### Active Directory

See [Active Directory variables](./COMMON.md##ActiveDirectory) in `common role`.

### Preflight Binary

* `client_preflight_timeout` sets timeout for port checks in seconds.

    Default value is: 
    ```yaml
    client_preflight_checks: 5
    ```

* `client_preflight_timesync` enables time synchronization of client if needed.

    Default value is: 
    ```yaml
    client_preflight_timesync: false
    ```

* `client_preflight_extra_args` allows passing additional arguments to the preflight binary.

    Default value is: 
    ```yaml
    client_preflight_extra_args:
    ```

### Facts generation

Facts generation variable defaults for all roles are set by variables in the `common role` and can be overriden for all roles by setting the appropriate `common role` variable.  See [common role facts generation variables](./COMMON.md##FactsGeneration) in `common role`.

* `client_preflight_facts_generate` enables facts generation.  Implicitely enabled if `client_preflight_reports_generate` is set.

    Default value is: 
    ```yaml
    client_preflight_facts_generate: "{{ facts_generate }}"
    ```

* `client_preflight_facts_verbose` enables verbose facts generation.

    Default value is: 
    ```yaml
    client_preflight_facts_verbose: "{{ facts_verbose }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the `common role` and can be overriden for all roles by setting the appropriate `common role` variable.  See [common role reports generation variables](./COMMON.md##ReportsGeneration) in `common role`.

* `client_preflight_reports_generate` enables report generation.  Reports are generated at the end of a `client_preflight` run for all hosts.

    Default value is: 
    ```yaml
    client_preflight_reports_generate: "{{ reports_generate }}"
    ```

  Disabling report generation if not needed will increase the speed of the `client_preflight` role.

* `client_preflight_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    client_preflight_reports_backup: "{{ reports_backup }}"

    ```

* `client_preflight_reports_details_format` sets the format of the details section in both the HTML and CSV reports.  Valid options:
    * `yaml` details will be in YAML format
    * `json` details will be in JSON format

    Default value is: 
    ```yaml
    client_preflight_reports_details_format: "{{ reports_details_format }}"

    ```

* `client_preflight_reports_host` sets the host on which the reports should be generated. 

    Default value is: 
    ```yaml
    client_preflight_reports_host: "{{ reports_host }}"
    ```

* `client_preflight_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `client_preflight` role.

  Default value is:
    ```yaml
    client_preflight_reports: 
      - src:  client_preflight_report.csv.j2   
        dest: client_preflight_report.csv
      - src:  client_preflight_report.html.j2
        dest: client_preflight_report.html
    ```
  
  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `client_preflight` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `client_preflight_reports_host`.  If `client_preflight_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Plugins

The `client_preflight` role contains a plugin to support operation of the role:

* `preflight` module performs preflight tasks on host by wrapping the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) preflight binary.

## Usage

Below is a sample playbook using the `client_preflight` role.

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

    # Directories
    client_sw_dir: "./files/QAS-4.2.3.25456/client"
    client_sw_tmp_dir: /tmp/1id

    # Facts
    client_preflight_facts_generate: true
    client_preflight_facts_verbose: true

    # Reports
    client_preflight_reports_generate: true
    client_preflight_reports_backup: false 

  roles:
    - name: oneidentity.authentication_services.client_preflight
```

See sample [HTML](http://htmlpreview.github.io/?https://github.com/OneIdentity/ansible-authentication-services/blob/master/docs/client_preflight_report.html) and [CSV](client_preflight_report.csv) reports generated from a run of this sample playbook.

For a copy of this and other sample playbooks see [examples](../examples/README.md)
