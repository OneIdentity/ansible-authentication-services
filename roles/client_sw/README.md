# `client_sw` Role

The `client_sw` role manages the deployment of [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software.  The role supports client software install, upgrade, downgrade, uninstall, and version checking.  Report generation can be enabled to provide CSV and HTML reports of the client software state before, changes made, and state after the role is run.

## Requirements

The role requires the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software install packages be available on Ansible control node.  See [variables](#variables) section for more detail.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information. 

### Client Software Directories

See [client software directories variables](../common/README.md#client-software-directories) in the [`common`](../common/README.md) role.

### Client software state

* `client_sw_pkgs` is a dictionary containing the client software packages and their state for your environment.  Possible state values:

    * `check` checks install state and reads version, no changes to the system   
    * `present` ensures package is installed and the same version as the install package in `client_sw_dir`
    * `absent` ensures package is not installed

    Default value is:

    ```yaml
    client_sw_pkgs:
      vasclnt: check 
      vasclnts: check 
      vasgp: check 
      vasgps: check 
      vassc: check 
      vascert: check 
      dnsupdate: check 
      pamdefender: check 
      vasyp: check 
      vasqa: check 
      vasproxy: check 
      vasdev: check 
    ```

    The default value for `client_sw_pkgs` contains all [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) packages with a state of `check` which will not make any changes to your hosts.  You'll need to override this variable to perform install, upgrade, downgrade, and uninstall of client software packages. 

    For example, if you wanted to make sure vasclnt and vasgp are installed and up to date in your environment and you don't use any other packages then `client_sw_pkgs` would be set as follows:

    ```yaml
    client_sw_pkgs:
      vasclnt: present 
      vasgp: present 
    ```

### Facts generation

Facts generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role facts generation variables](../common/README.md#facts-generation) in the [`common`](../common/README.md) role.

* `client_sw_facts_generate` enables facts generation.  Implicitely enabled if `client_sw_reports_generate` is set.

    Default value is: 
    ```yaml
    client_sw_facts_generate: "{{ facts_generate }}"
    ```

* `client_sw_facts_verbose` enables verbose facts generation.

    Default value is: 
    ```yaml
    client_sw_facts_verbose: "{{ facts_verbose }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role report generation variables](../common/README.md#report-generation) in the [`common`](../common/README.md) role.

* `client_sw_reports_generate` enables report generation.  Reports are generated at the end of a `client_sw` run for all hosts.

    Default value is: 
    ```yaml
    client_sw_reports_generate: "{{ reports_generate }}"
    ```

  Disabling report generation if not needed will increase the speed of the `client_sw` role.

* `client_sw_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    client_sw_reports_backup: "{{ reports_backup }}"

    ```

* `client_sw_reports_details_format` sets the format of the details section in both the HTML and CSV reports.  Valid options:
    * `yaml` details will be in YAML format
    * `json` details will be in JSON format

    Default value is: 
    ```yaml
    client_sw_reports_details_format: "{{ reports_details_format }}"

    ```

* `client_sw_reports_host` sets the host on which the reports should be generated. 

    Default value is: 
    ```yaml
    client_sw_reports_host: "{{ reports_host }}"
    ```

* `client_sw_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `client_sw` role.

  Default value is:
    ```yaml
    client_sw_reports: 
      - src:  client_sw_report.csv.j2   
        dest: client_sw_report.csv
      - src:  client_sw_report.html.j2
        dest: client_sw_report.html
    ```
  
  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `client_sw` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `client_sw_reports_host`.  If `client_sw_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Plugins

The `client_sw` role contains a few plugins to support operation of the role:

* `client_sw_pkgs` module checks and parses the subdirectories in the directory specified in `client_sw_dir` to find the correct packages for each host per its OS distribution and hardware architecture. 

* `pkgdict2items` filter performs client software package sorting by state and name, and formats the result in the format expected by Ansible for use in looping.

## Usage

Below is a sample playbook using the `client_sw` role that will install, upgrade, or downgrade the `vasclnt`, `vasgp`, `vassc`, and `pamdefender` packages for all hosts so that after the playbook run they will the same versions as the packages found in `client_sw_dir`. 

Only the `client_sw_dir` and `client_sw_pkgs` variables are overriden in this playbook so the default values will be used for all other variables.

```yaml
---

- hosts: all 

  vars:

    # Directories
    client_sw_dir: "./files/QAS-4.2.3.25456/client"

    # Packages
    client_sw_pkgs:
      vasclnt: present
      vasgp: present
      vassc: present
      pamdefender: present

    # Facts
    client_sw_facts_generate: true
    client_sw_facts_verbose: false

    # Reports
    client_sw_reports_generate: true 
    client_sw_reports_backup: false 

  roles:
    - name: oneidentity.authentication_services.client_sw
```

For a copy of this and other sample playbooks see [examples](../../examples/README.md)
