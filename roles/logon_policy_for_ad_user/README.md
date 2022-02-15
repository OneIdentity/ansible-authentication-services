# `logon_policy_for_ad_user` Role

The `logon_policy_for_ad_user` role creates CSV and HTML reports that list the hosts where Active Directory users have been granted log on permission.

## Variables

All of the variables shown below have a default value but can be overridden to suit your environment.  Variable overriding can be done in playbooks, inventories, from the command line using the `-e` switch with the `ansible-playbook` command, or from Ansible Tower and AWX.  See [Ansbile documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html) for further information.

### Report parameters

* `logon_policy_for_ad_user_user_name`: An Active Directory user can be specified in the following format: DOMAIN\SamAccountName.  For example: EXAMPLE\jason.  Reports will be generated for the specified user.  If no user is specified then the reports will be generated for all Active Directory users who have been granted log on permission.

    Default value is:
    ```yaml
    logon_policy_for_ad_user_user_name: ''
    ```

### Facts generation

Facts generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role facts generation variables](../common/README.md#facts-generation) in the [`common`](../common/README.md) role.

* `logon_policy_for_ad_user_facts_generate` enables facts generation.  Implicitely enabled if `logon_policy_for_ad_user_reports_generate` is set.

    Default value is:
    ```yaml
    logon_policy_for_ad_user_facts_generate: "{{ facts_generate }}"
    ```

### Report generation

Report generation variable defaults for all roles are set by variables in the [`common`](../common/README.md) role and can be overriden for all roles by setting the appropriate [`common`](../common/README.md) role variable.  See [common role report generation variables](../common/README.md#report-generation) in the [`common`](../common/README.md) role.

* `logon_policy_for_ad_user_reports_generate` enables report generation.  Reports are generated at the end of a `logon_policy_for_ad_user` run for all hosts.

    Default value is: 
    ```yaml
    logon_policy_for_ad_user_reports_generate: "{{ reports_generate }}"
    ```

* `logon_policy_for_ad_user_reports_backup` enables backup of prior reports by renaming them with the date and time they were generated so that the latest reports do not override the previous reports.

    Default value is: 
    ```yaml
    logon_policy_for_ad_user_reports_backup: "{{ reports_backup }}"

    ```

* `logon_policy_for_ad_user_reports_host` sets the host on which the reports should be generated.

    Default value is: 
    ```yaml
    logon_policy_for_ad_user_reports_host: "{{ reports_host }}"
    ```

* `logon_policy_for_ad_user_reports` is a list of dictionaries that define the reports to be generated.  The default value creates a CSV and HTML report using the templates included with the `logon_policy_for_ad_user` role.

  Default value is:
    ```yaml
    logon_policy_for_ad_user_reports:
      - src:  logon_policy_for_ad_user_report.csv.j2
        dest: logon_policy_for_ad_user_report.csv
      - src:  logon_policy_for_ad_user_report.html.j2
        dest: logon_policy_for_ad_user_report.html
    ```

  The `src` key for each list entry is the report template file on the Ansible control node.  With a relative path Ansible will look in the `logon_policy_for_ad_user` role `template` directory.  Use a absolute path to speciy templates located elsewhere on the Ansible control node.

  The `dest` key for each list entry is the report file on the machine specified in `logon_policy_for_ad_user_reports_host`.  If `logon_policy_for_ad_user_reports_host` is set to the Ansible control node a relative path can be used and it will be relative to the directory from which the playbook is run.  For other hosts, an absolute path must be used.  In either case the containing directory must exist.

## Usage

Below is a sample playbook using the `logon_policy_for_ad_user` role.

```yaml
---

- hosts: all
  gather_facts: false

  # The variables you would most likely want/need to override have been included
  vars:

    # Report parameters
    logon_policy_for_ad_user_user_name: ''

    # Facts
    logon_policy_for_ad_user_facts_generate: true

    # Reports
    logon_policy_for_ad_user_reports_generate: true
    logon_policy_for_ad_user_reports_backup: false

  roles:
    - name: oneidentity.authentication_services.logon_policy_for_ad_user
```

For a copy of this and other sample playbooks see [examples](../../examples/README.md)
