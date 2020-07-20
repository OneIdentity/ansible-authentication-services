# `client_config` Role

The `client_config` role performs [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client configuration by adding, modifying, and removing entries from the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) configuration files on the client.  Report generation can be enabled to provide CSV and HTML reports of the results.

## Requirements

The role requires the [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) client software be installed on the client.  See the [`client_sw`](../client_sw/README.md) role for how to peform client software installation using Ansible.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information. 

### Top-level Default Settings

* `client_config_create` sets the default setting for configuration file creation.  Possible values are:

    * `yes` create file if not present
    * `no` do not create file if not present which will result in a failure

    Default value is:
    ```yaml
    client_config_create: yes
    ```

* `client_config_mode` sets the default setting for configuration file permissions.  Possible values are either blank which uses the default mode per the umask set for the user account used by Ansible on the host, or a string with the desired mode in octal (like '644') or in symolic mode (like 'u=rw,g=r,o=r')

    Default value is:
    ```yaml
    client_config_mode:
    ```

* `client_config_owner` sets the default setting for configuration file owner.  Possible values are either blank which uses the owner of the account Ansible is using on the host for file creation and does not modify the owner when the file is modified, or a string containing the desired owner.

    Default value is:
    ```yaml
    client_config_owner:
    ```

* `client_config_group` sets the default setting for configuration file group.  Possible values are either blank which uses the group of the account Ansible is using on the host for file creation and does not modify the group when the file is modified, or a string containing the desired group.

    Default value is:
    ```yaml
    client_config_group:
    ```

* `client_config_backup` sets the default setting for configuration file backup.  This creates a backup of the file every time it is modified by Ansible.  Each backup file has the name and time of the backup as part of the file name.  Backup files are not automatically removed so their removal needs to be managed when this option is enabled.  Possible values are:

    * `yes` create backup of file before modifications
    * `no` do not create backup of file

    Default value is:
    ```yaml
    client_config_backup: yes
    ```

### Configuration Files

The contents, creation, backup, and permissions of each configuration file are specified by a set of variables for each configuration file.  All configuration files have the same seven variables.  The variables are named as shown below with `FILE_NAME` being replaced by the name of the configuration file with any `.`'s in the file name nbeing replace with an `_`.  For instance, for the `vas.conf` file, `FILE_NAME` would be replaced in the variable names below with `vas_conf`.

* `client_config_FILE_NAME` is a list of items to set or clear in the file.  The format of the items will vary by configuration file and will be specified in the section for each file found below.

    Default values is:
    ```yaml
    client_config_FILE_NAME: []
    ```

* `client_config_FILE_NAME_create` enables the creation of the file if it doesn't exist.

    Default value is:
    ```yaml
    client_config_FILE_NAME_create: "{{ client_config_create }}
    ```

* `client_config_FILE_NAME_mode` sets the file permissions for the file when it is created or modified.  Leave unchanged to create the file with default permissions per the umask set on the host system and to not modify permissions when the file is modified.

    Default value is:
    ```yaml
    client_config_FILE_NAME_mode: "{{ client_config_mode }}
    ```

* `client_config_FILE_NAME_owner` sets the file owner for the file when it is created or modified.  Leave unchanged to create the file with the owner set to the account Ansible is using on the host and to not modify the owner when the file is modified.

    Default value is:
    ```yaml
    client_config_FILE_NAME_owner: "{{ client_config_owner }}
    ```

* `client_config_FILE_NAME_group` sets the file group for the file when it is created or modified.  Leave unchanged to create the file with the group set to the account Ansible is using on the host and to not modify the group when the file is modified.

    Default value is:
    ```yaml
    client_config_FILE_NAME_group: "{{ client_config_group }}
    ```

* `client_config_FILE_NAME_backup` sets creating a backup copy of the file every time it is modified by Ansible.  Each backup file has the name and time of the backup as part of the file name.  Removal of these backups is not automatically handled and would need to be managed separately.

    Default value is:
    ```yaml
    client_config_FILE_NAME_backup: "{{ client_config_backup }}
    ```

#### vas.conf

The `vas.conf` configuration file is formatted per standard [INI file](https://en.wikipedia.org/wiki/INI_file) conventions.  See [Safeguard Authentication Services vas.conf docs](https://support.oneidentity.com/technical-documents/authentication-services/4.2.4/administration-guide/7#TOPIC-1467970) for further information on valid sections and options for this file.

The Ansible `ini_file` module is used for formatting this file.  See [Ansible ini_file module docs](https://docs.ansible.com/ansible/latest/modules/ini_file_module.html#ini-file-module) for details on this module.

Please see top of the [Configuration Files](#configuration-files) section for the variables that control creation, backup, and permissions of this file but not its content.  The variable that controls its content is shown below.

* `client_config_vas_conf` is a list of items to set or clear in `vas.conf`

    Each item in this list can contain the following fields:

    * `state`
        * Required
        * Valid values:
            * `present`
            * `absent`
    * `section`
        * Required
    * `option`
        * Optional
        * Omitted if not set.  Caution, please note that if `state` is set to `absent` and `option` is not set then the entire specified `section` will be removed
    * `value`
        * Optional
        * Default value is empty string

#### user-override and group-override

The `user-override` and `group-override` configuration files allow per-host, local mapping between Active Directory and local users and groups.  See [Safeguard Authentication Services docs](https://support.oneidentity.com/technical-documents/authentication-services/4.2.4/administration-guide/36#TOPIC-1468088) for further information on the format of these files.

The Ansible `lineinfile` module is used for formatting these files.  See [Ansible lineinfile module docs](https://docs.ansible.com/ansible/latest/modules/lineinfile_module.html#lineinfile-module) for details on this module.

Please see top of the [Configuration Files](#configuration-files) section for the variables that control creation, backup and permissions of these files but not their content.  The variables that control their content are shown below.

* `client_config_user_override` and `client_config_group_override` are a list of items to set or clear in `user-override` and `user-override`

    Each item in this list can contain the following fields:

    * `state`
        * Required
        * Valid values:
            * `present`
            * `absent`
    * `line`
        * Optional
        * Default value is empty string.  Line to be set or cleared from file depending on `state`.  If `regex` is not set this line has to EXACTLY match an existing line for it to be removed when `state` is `absent` 
    * `regex`
        * Optional
        * Omitted if not set.  Used to match an existing line so that it can be cleared or modified.  If `regex` is found and `insertafter` or `insertbefore` are not specified then the matched line will be removed or replaced depending on `state`.  If `regex` is not found and `state` is present then `line` will be added to the end of the file.
    * `insertafter`
        * Optional
        * Omitted if not set.  In the case of a `regex` match will insert `line` on the line after the match.
    * `insertbefore`
        * Optional
        * Omitted if not set.  In the case of a `regex` match will insert `line` on the line before the match.

#### users.allow, users.deny, groups.allow, and groups.deny

The `users.allow`, `users.deny`, `groups.allows` and `groups.deny` configuration files allow per-host, local control of allowed and denied users and groups.  See [Safeguard Authentication Services docs](https://support.oneidentity.com/technical-documents/authentication-services/4.2.4/administration-guide/31#TOPIC-1468068) for further information on the format of these files.

The Ansible `lineinfile` module is used for formatting these files.  See [Ansible lineinfile module docs](https://docs.ansible.com/ansible/latest/modules/lineinfile_module.html#lineinfile-module) for details on this module.

Please see top of the [Configuration Files](#configuration-files) section for the variables that control creation, backup and permissions of these files but not their content.  The variables that control their content are shown below.

* `client_config_users_allow`, `client_config_users_deny`, `client_config_groups_allow` and `client_config_groups_deny` are a list of items to set or clear in `users.allow`, `users.deny`, `groups.allow` and `groups.deny`

    Each item in this list can contain the following fields:

    * `state`
        * Required
        * Valid values:
            * `present`
            * `absent`
    * `line`
        * Optional
        * Default value is empty string.  Line to be set or cleared from file depending on `state`.  If `regex` is not set this line has to EXACTLY match an existing line for it to be removed when `state` is `absent`.  Most use cases for these files would likely use the `regex` field
    * `regex`
        * Optional
        * Omitted if not set.  Used to match an existing line so that it can be cleared or modified.  If `regex` is found and `insertafter` or `insertbefore` are not specified then the matched line will be removed or replaced depending on `state`.  If `regex` is not found and `state` is present then `line` will be added to the end of the file.
    * `insertafter`
        * Optional
        * Omitted if not set.  In the case of a `regex` match will insert `line` on the line after the match.
    * `insertbefore`
        * Optional
        * Omitted if not set.  In the case of a `regex` match will insert `line` on the line before the match.

#### users.starling

The `users.starling` configuration file is for per-host, local configuration of Starling.  See [Safeguard Authentication Services docs](https://support.oneidentity.com/technical-documents/authentication-services/4.2.4/administration-guide/44#TOPIC-1468117) for further information on the format of this file.

The Ansible `lineinfile` module is used for formatting this file.  See [Ansible lineinfile module docs](https://docs.ansible.com/ansible/latest/modules/lineinfile_module.html#lineinfile-module) for details on this module.

Please see top of the [Configuration Files](#configuration-files) section for the variables that control creation, backup and permissions of this file but not its content.  The variable that control its content is shown below.

* `client_config_users_starling` is a list of items to set or clear in `users.starling`

    Each item in this list can contain the following fields:

    * `state`
        * Required
        * Valid values:
            * `present`
            * `absent`
    * `line`
        * Optional
        * Default value is empty string.  Line to be set or cleared from file depending on `state`.  If `regex` is not set this line has to EXACTLY match an existing line for it to be removed when `state` is `absent`.  Most use cases for this file would likely use the `regex` field
    * `regex`
        * Optional
        * Omitted if not set.  Used to match an existing line so that it can be cleared or modified.  If `regex` is found and `insertafter` or `insertbefore` are not specified then the matched line will be removed or replaced depending on `state`.  If `regex` is not found and `state` is present then `line` will be added to the end of the file.
    * `insertafter`
        * Optional
        * Omitted if not set.  In the case of a `regex` match will insert `line` on the line after the match.
    * `insertbefore`
        * Optional
        * Omitted if not set.  In the case of a `regex` match will insert `line` on the line before the match.

### Facts generation

Facts generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role facts generation variables](../common/README.md#facts-generation) in the [`common`](../common/README.md) role.

* `client_config_facts_generate` enables facts generation.  Implicitely enabled if `client_config_reports_generate` is set.

    Default value is: 
    ```yaml
    client_join_facts_generate: "{{ facts_generate }}"
    ```

* `client_config_facts_verbose` enables verbose facts generation.

    Default value is: 
    ```yaml
    client_config_facts_verbose: "{{ facts_verbose }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) variable.  See [common role reports generation variables](../common/README.md#report-generation) in the [`common`](../common/README.md) role.

* `client_config_reports_generate` enables report generation.  Reports are generated at the end of a `client_config` run for all hosts.

    Default value is: 
    ```yaml
    client_config_reports_generate: "{{ reports_generate }}"
    ```

  Disabling report generation if not needed will increase the speed of the `client_config` role.

* `client_config_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    client_config_reports_backup: "{{ reports_backup }}"

    ```

* `client_config_reports_details_format` sets the format of the details section in both the HTML and CSV reports.  Valid options:
    * `yaml` details will be in YAML format
    * `json` details will be in JSON format

    Default value is: 
    ```yaml
    client_config_reports_details_format: "{{ reports_details_format }}"

    ```

* `client_config_reports_host` sets the host on which the reports should be generated. 

    Default value is: 
    ```yaml
    client_config_reports_host: "{{ reports_host }}"
    ```

* `client_config_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `client_config` role.

  Default value is:
    ```yaml
    client_config_reports: 
      - src:  client_config_report.csv.j2   
        dest: client_config_report.csv
      - src:  client_config_report.html.j2
        dest: client_config_report.html
    ```
  
  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `client_config` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `client_config_reports_host`.  If `client_config_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Plugins

The `client_config` role contains a plugin to support operation of the role:

* `dictlistselect` filter takes a list of dicts and returns a new list of dicts that only includes the specified keys.

## Usage

Below is a sample playbook using the `client_config` role.

```yaml
---

- hosts: all 
  gather_facts: false

  vars:

    # vas.conf settings
    client_config_vas_conf:
      - section: libdefaults
        option: ticket_lifetime
        value: 20h
        state: present

    # users.allow settings
    client_config_user_allow:
      - line: 'SAMPLE\user'
        state: present
      - line: 'SAMPLE\guest'
        state: absent

    # users.deny settings
    client_config_user_allow:
      - line: 'SAMPLE\user'
        state: absent
       - line: 'SAMPLE\guest'
        state: present

    # Facts
    client_config_facts_generate: true
    client_config_facts_verbose: false

    # Reports
    client_config_reports_generate: true 
    client_config_reports_backup: false 

  roles:
    - name: oneidentity.authentication_services.client_config
```

For a copy of this and other sample playbooks see [examples](../../examples/README.md)
