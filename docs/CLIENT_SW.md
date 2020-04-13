# `client_sw` Role

The `client_sw` role manages the deployment of [Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software.  The role supports client software install, upgrade, downgrade, uninstall, and version checking.  Report generation can be enabled to provide CSV and HTML reports of the state before, action taken, and state after for all hosts and software packages.

## Requirements

The role requires the [Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software install directory be available on Ansible control node.  See [variables](##Variables) for more detail.

## Variables

All of the variables shown below have a default value but can be overriden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` swith with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information. 

### Directories

* `client_sw_dir` should be set to the `client` directory on the [Authentication Services](https://www.oneidentity.com/products/authentication-services/) install ISO.  The entire ISO can be mounted or just this subdirectory copied to the Ansible control node.  The subdirectories of the `client` directory contain install packages for all supported systems and architectures.  Only the systems and architectures needed for your environment need to be included.   

    Default value is: 
    ```yaml
    client_sw_dir: /tmp/1id/client
    ```

    For example, the `client` directory on the [Authentication Services](https://www.oneidentity.com/products/authentication-services/) 4.2.3.25456 install ISO contains the following subdirectories:

    ```
    aix-71
    freebsd-x86_64
    hpux-ia64
    hpux-pa-11v3
    linux-aarch64
    linux-ia64
    linux-ppc64
    linux-ppc64le
    linux-s390
    linux-x86
    linux-x86_64
    macos-1012
    solaris10-sparc
    solaris10-x64
    ``` 

    but if your environment only has x86_64 Linux and MacOS client systems then your `client` directory would only need to contain the following subdirectories:

    ```
    linux-x86_64
    macos-1012
    ```

* `client_sw_tmp_dir` sets the temporary directory on Ansible hosts for storing files that need to be copied over to the hosts during software deployment operations.  The directory is created if it doesn't exist and is removed after all operations are completed.

    Default value is: 
    ```yaml
    client_sw_tmp_dir: /tmp/1id
    ```

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

    The default value for `client_sw_pkgs` contains all [Authentication Services](https://www.oneidentity.com/products/authentication-services/) packages with a state of `check` which will not make any changes to your hosts.  You'll need to override this variable to perform install, upgrade, downgrade, and uninstall of client software packages. 

    For example, if you wanted to make sure vasclnt and vasgp are installed and up to date in your environment and you don't use any other packages then `client_sw_pkgs` would be set as follows:

    ```yaml
    client_sw_pkgs:
      vasclnt: present 
      vasgp: present 
    ```

### Report generation

* `client_sw_reports_generate` enables report generation.  Reports are generated at the end of a `client_sw` role run for all hosts and all package specified in `client_sw_pkgs`

  Default value is: 
  ```yaml
  client_sw_reports_generate: true
  ```

  Disabling report generation if not needed will increase the speed of the `client_sw` role.

* `client_sw_reports_soft_fail` enables masking Ansible failures for software install failures and allows the host to continue to run even after a failure.  The failures will be shown in the report but not in the Ansible run summary.  This only has an effect if `client_sw_reports_generate` is enabled.

  Default value is: 
  ```yaml
  client_sw_reports_soft_fail: true
  ```

* `client_sw_reports_hide_nops` enables suppressing lines in the report for packages on a host for which there is not an installer package present and the package is not installed on the host.  This is useful if you specify a package in `client_sw_pkgs` that is only available for some system so that is doesn't show up in the report for non-supported systems.

  Default value is: 
  ```yaml
  client_sw_reports_hide_nops: true
  ```

* `client_sw_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

  Default value is: 
  ```yaml
  client_sw_reports_backup: false
  ```

* `client_sw_reports_host` is the machine on which the reports should be generated.  The default is the Ansible control node.

  Default value is: 
  ```yaml
  client_sw_reports_host: 127.0.0.1
  ```

* `client_sw_reports` is a list of dictionaries that contain the reports to be generated.  The default value creates a CSV and HTML report using the templates includes with the `client_sw` role.

  Default value is:

  ```yaml
  client_sw_reports: 
    - src:  client_sw_report.csv.j2   
      dest: client_sw_report.csv
    - src:  client_sw_report.html.j2
      dest: client_sw_report.html
  ```
  
  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will lokk in the `client_sw` role `template` directory.  Use a absolute path to specify templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `client_sw_reports_host`.  If `client_sw_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an abosolute path must be used.  In either case the containing directory must exist.

## Plugins

The `client_sw` role contains a few plugins to support operation of the role:

* `client_sw_pkg_dir` module checks and parses the subdirectories in the directory specified in `client_sw_dir` to find the correct packages for each host per its OS distribution and hardware architecture. 

* `pkgdict2items` filter performs client software package sorting by state and name, and formats the result in the format expected by Ansible for use in looping.

## Usage

Below is a sample playbook using the `client_sw` role that will install, upgrade, or downgrade the `vasclnt`, `vasgp`, `vassc`, and `pamdefender` packages for all hosts so that after the playbook run they will the same versions as the packages found in `client_sw_dir`. 

Only the `client_sw_dir` and `client_sw_pkgs` variables are overriden in this playbook so the default values will be used for all other variables.

```yaml
---

- hosts: all 

  vars:

    client_sw_dir: "./files/QAS-4.2.3.25456/client"

    client_sw_pkgs:
      vasclnt: present
      vasgp: present
      vassc: present
      pamdefender: present

  roles:
    - name: oneidentity.authentication_services.client_sw
```

See sample [HTML](http://htmlpreview.github.io/?https://github.com/OneIdentity/ansible-authentication-services/blob/master/docs/client_sw_report.html) and [CSV](client_sw_report.csv) reports generated from a run of this sample playbook.

For a copy of this and other sample playbooks see [examples](../examples/README.md)
