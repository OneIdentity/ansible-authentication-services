# `common` Role

The `common` role contains common tasks and variables required by other roles and is automatically included in all other roles.  

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information. 

### Client Software Directories

* `client_sw_dir` should be set to the `client` directory of the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) installation ISO.  The entire ISO can be mounted or just this subdirectory copied to the Ansible control node.  The subdirectories of the `client` directory contain install packages for all supported systems and architectures.  Only the systems and architectures needed for your environment need to be included.   

    Default value is: 
    ```yaml
    client_sw_dir: /tmp/1id/client
    ```

    For example, the `client` directory on the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) 4.2.3.25456 install ISO contains the following subdirectories:

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

* `client_sw_tmp_dir` sets the temporary directory on Ansible hosts for storing files that need to be copied over to the hosts during software deployment operations.  The directory is created if it doesn't exist.

    Default value is: 
    ```yaml
    client_sw_tmp_dir: /tmp/1id
    ```

### Active Directory

* `client_domain` sets the Active Directory domain that will be used by the `client_preflight` and `client_join` roles.

    Default value is: 
    ```yaml
    client_domain:
    ```

* `client_username` sets the user or principal to perform Active Directory readiness and join/unjoin operations.  Secrets do not have to be provided in plain text, see [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html) for futher information.

    Default value is: 
    ```yaml
    client_username:
    ```

* `client_password` sets the password used to authenticate the user or principal with Active Directory.  Secrets do not have to be provided in plain text, see [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html) for futher information.

    Default value is: 
    ```yaml
    client_password:
    ```

* `client_servers` sets a list of domain controllers to use for checks.  This is optional as the default domain controller will be detected through DNS and LDAP lookups.

    Default value is: 
    ```yaml
    client_servers: []
    ```

* `client_account_name` sets the name of the computer account for the host in Active Directory. This is optoinal as the default will generate a name based on the host's DNS name.

    Default value is: 
    ```yaml
    client_account_name:
    ```

* `client_account_container` sets the name of the computer account container for the host in Active Directory. This is optional and the default is the default computers container in Active Directory. 

    Default value is: 
    ```yaml
    client_account_container:
    ```

### Facts generation

Facts generation variable defaults for all roles are set by the variables below.

* `facts_generate` enables facts generation.  Implicitely enabled if `reports_generate` is set.

    Default value is: 
    ```yaml
    facts_generate: true
    ```

* `facts_verbose` enables verbose facts generation.

    Default value is: 
    ```yaml
    facts_verbose: true
    ```

### Report generation

Report generation variable defaults for all roles are set by the variables below.

* `reports_generate` enables report generation.

    Default value is: 
    ```yaml
    reports_generate: true
    ```

  Disabling report generation if not needed will increase the speed of all roles.

* `reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    reports_backup: false

    ```

* `reports_details_format` sets the format of the details section in both the HTML and CSV reports.  Valid options:
    * `yaml` details will be in YAML format
    * `json` details will be in JSON format

    Default value is: 
    ```yaml
    reports_details_format: yaml

    ```

* `reports_host` sets the host on which the reports should be generated. 

    Default value is: 
    ```yaml
    reports_host: '127.0.0.1'
    ```
