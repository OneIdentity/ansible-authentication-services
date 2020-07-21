**One Identity open source projects are supported through [One Identity GitHub issues](https://github.com/OneIdentity/ars-ps/issues) and the [One Identity Community](https://www.oneidentity.com/community/). This includes all scripts, plugins, SDKs, modules, code snippets or other solutions. For assistance with any One Identity GitHub project, please raise a new Issue on the [One Identity GitHub project](https://github.com/OneIdentity/ars-ps/issues) page. You may also visit the [One Identity Community](https://www.oneidentity.com/community/) to ask questions.  Requests for assistance made through official One Identity Support will be referred back to GitHub and the One Identity Community forums where those requests can benefit all users.**

# Safeguard Authentication Services Ansible Collection

The One Identity Safeguard Authentication Services Ansible Collection, referred to as `ansible-authentication-services`, consists of roles, modules, plugins, report templates, and sample playbooks to automate software deployment, configuration, Active Directory joining, profiling, and report generation for [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/). 

## Collection Contents

### Implemented

* [`common role`](roles/common/README.md): Common tasks and variables required by other roles.

* [`client_sw role`](roles/client_sw/README.md): Client software install, upgrade, downgrade, uninstall, and version checking.
    * [`client_sw_pkgs module`](roles/client_sw/README.md#plugins) Client software install package directory checking. 
    * [`pkgdict2items filter`](roles/client_sw/README.md#plugins) Client software package sorting by state and name.

* [`client_preflight role`](roles/client_preflight/README.md): Check client readiness for software install and AD join.
    * [`preflight module`](roles/client_preflight/README.md#plugins) Performs preflight tasks on host.

* [`client_join role`](roles/client_join/README.md): Client Active Directory joining/unjoining. 
    * [`vastool_join module`](roles/client_join/README.md#plugins) Performs Active Directory join/unjoin tasks on host.

* [`client_config role`](roles/client_config/README.md): Client configuration.
    * [`dictlistselect filter`](roles/client_config/README.md#plugins) Filter list of dicts to only include specified keys.

### In Development 

* [`client_profile role`](docs/CLIENT_PROFILE.md): Client profiling. 

### Future

* [`server_sw role`](docs/SERVER_SW.md): Active Directory Server software install, upgrade, downgrade, uninstall, and version checking. 

* [`server_config role`](docs/SERVER_CONFIG.md): Active Directory Server configuration. 

* [`server_profile role`](docs/SERVER_PROFILE.md): Active Directory Server profiling. 

## Installation

### Prerequisites

* [Ansible](https://github.com/ansible/ansible) version 2.9 or later

    * `Collections are a new feature introduced in Ansible version 2.9.  Please use the latest 2.9+ release for the best user experience.`

* One Identity [Safeguard Authentication Services](https://www.oneidentity.com/products/authentication-services/) version 4.2.x or later

    * `This collection expects the components and structure of Safeguard Authentication Services 4.2.x or later.`
    * See collection role [documentation](docs/) for specific, per-role  requirements and instructions.
    * See One Identity [Safeguard Authentication Services documentation](https://support.oneidentity.com/authentication-services/4.2.4/technical-documents) for requirements and instructions.

### From Ansible Galaxy 

To install from [Ansible Galaxy](https://galaxy.ansible.com/) you can use the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command to install the collection on your control node.  See [Ansible documentation](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html#installing-collections) for futher information.

Using `ansible-galaxy` command:
```bash
ansible-galaxy collection install oneidentity.authentication_services
```

The collection can also be added to a project's `requirements.yml` file
```yaml
---
collections:
  - name: oneidentity.authentication_services
```

and installed using the `ansible-galaxy` command.  This method allows all required collections for a project to be specified in one place and installed with one command.
```bash
ansible-galaxy collection install -r requirements.yml
```

When used with [Ansible Tower](https://www.ansible.com/products/tower) and [Ansible AWX](https://github.com/ansible/awx) the collections in the project's `requirements.yml` file are automatically installed each time a project is run and there is no need to use the `ansible-galaxy` command.

### From GitHub

For the examples in this section please see `ansible-authentication-services` [releases page](https://github.com/OneIdentity/ansible-authentication-services/releases) to find the latest collection build artifact (*.tar.gz file) and use the URL to this file in place of the URL's shown below.  The collection build artifact is under the 'Assets' section for each release (right click on the *.tar.gz file and select 'Copy link address' to copy URL).

To install from [GitHub](https://github.com/OneIdentity/ansible-authentication-services) you can use the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command to install the collection on your control node.  See [Ansible documentation](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html#installing-collections) for futher information.

Using `ansible-galaxy` command:
```bash
ansible-galaxy collection install https://github.com/OneIdentity/ansible-authentication-services/releases/download/v0.0.5/oneidentity-authentication_services-0.0.5.tar.gz
```

The collection can also be added to a project's `requirements.yml` file
```yaml
---
collections:
  - name: https://github.com/OneIdentity/ansible-authentication-services/releases/download/v0.0.5/oneidentity-authentication_services-0.0.5.tar.gz
```

and installed using the `ansible-galaxy` command.  This method allows all required collections for a project to be specified in one place and installed with one command.
```bash
ansible-galaxy collection install -r requirements.yml
```

When used with [Ansible Tower](https://www.ansible.com/products/tower) and [Ansible AWX](https://github.com/ansible/awx) the collections in the project's `requirements.yml` file are automatically installed each time a project is run and there is no need to use the `ansible-galaxy` command.

### Local Build and Install

For local build and installation, you can clone the Git repository, build the collection artifact, and install the locally built collection artifact.  This would be useful for those wishing to extend or customize the collection.

1. Clone the Git repository:

    ```bash
    git clone https://github.com/OneIdentity/ansible-authentication-services.git
    ```

2. Run a local build inside the collection using the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command in the root directory of the cloned repository:

    ```bash
    cd ansible-authentication-services
    ansible-galaxy collection build
    ```

    The build command will generate an Ansible Galaxy collection artifact with a `tar.gz` file extension, sample output will look like the following:

    ```
    Created collection for oneidentity.authentication_services at /home/user/ansible-authentication-services/oneidentity-authentication_services-0.0.5.tar.gz
    ```

    `Pleae note the path shown above is just an example, the path to your build artifact will be in the root directory of the cloned repository.`

3. Install the locally-built collection artifact using the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command to install the collection on your control node.  See [Ansible documentation](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html#installing-collections) for futher information.

    Using `ansible-galaxy` command:

    ```bash
    ansible-galaxy collection install /home/user/ansible-authentication-services/oneidentity-authentication_services-0.0.5.tar.gz
    ```

    The collection can also be added to a project's `requirements.yml` file
    ```yaml
    ---
    collections:
    - name: /home/user/ansible-authentication-services/oneidentity-authentication_services-0.0.5.tar.gz
    ```

    and installed using the `ansible-galaxy` command.  This method allows all required collections for a project to be specified in one place and installed with one command.
    ```bash
    ansible-galaxy collection install -r requirements.yml
    ```

When used with [Ansible Tower](https://www.ansible.com/products/tower) and [Ansible AWX](https://github.com/ansible/awx) the collections in the project's `requirements.yml` file are automatically installed each time a project is run and there is no need to use the `ansible-galaxy` command.

## Usage

The collection provides various sample playbooks in the [examples](examples/README.md) directory. 

## Supported Platforms

All [Safeguard Authentication Services supported platforms](https://support.oneidentity.com/technical-documents/authentication-services/4.2.4/release-notes/2#TOPIC-1376245).

## Notes

### Known issues

* Check mode does not work as expected for the client_sw role.  No changes are made and it doesn't cause errors but the stated changes that would or would not be made if run normally are not accurate.
* The directory of client software install packages has to be on the Ansible control node.  It would be nice to be able to point to this directory on another machine but this is not possible at this time.
* The IPV4 address for HP-UX machines does not show up in the CSV and HTML reports, this is due to differences in how facts are reported for this OS.  No plan to fix this issue at this time.

### TODO's

* Implement client_profile role.
* Other roles/features depending on interest may include roles to automate server software deployment, server configuration, and server profiling.
