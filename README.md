**One Identity open source projects are supported through [One Identity GitHub issues](https://github.com/OneIdentity/ars-ps/issues) and the [One Identity Community](https://www.oneidentity.com/community/). This includes all scripts, plugins, SDKs, modules, code snippets or other solutions. For assistance with any One Identity GitHub project, please raise a new Issue on the [One Identity GitHub project](https://github.com/OneIdentity/ars-ps/issues) page. You may also visit the [One Identity Community](https://www.oneidentity.com/community/) to ask questions.  Requests for assistance made through official One Identity Support will be referred back to GitHub and the One Identity Community forums where those requests can benefit all users.**

# Authentication Services Ansible Collection

The One Identity Authentication Services Ansible Collection, referred to as `ansible-authentication-services`, consists of roles, modules, plugins, report templates, and sample playbooks to automate software deployment, configuration, Active Directory joining, profiling, and report generation for Authentication Services. 

## Collection Contents

### Implemented

* [`common role`](docs/COMMON.md): Common tasks and variables required by other roles
* [`client_sw role`](docs/CLIENT_SW.md): Client software install, upgrade, downgrade, uninstall, and version checking.
    * [`client_sw_pkg_dir module`](docs/CLIENT_SW.md#Plugins) Client software install package directory checking 
    * [`pkgdict2items filter`](docs/CLIENT_SW.md#Plugins) Client software package sorting by state and name

### In Development 

* [`client_join role`](docs/CLIENT_CONFIG.md): Client configuration and Active Directory joining. 
* [`client_profile role`](docs/CLIENT_PROFILE.md): Client profiling. 

### Future

* [`server_sw role`](docs/SERVER_SW.md): Active Directory Server software install, upgrade, downgrade, uninstall, and version checking. 
* [`server_config role`](docs/SERVER_CONFIG.md): Active Directory Server configuration. 
* [`server_profile role`](docs/SERVER_PROFILE.md): Active Directory Server profiling. 

## Installation

### Prerequisites

* [Ansible](https://github.com/ansible/ansible) version 2.9 or later

    * `Collections are a new feature of Ansible introduced in version 2.9.  Please use the latest 2.9 release for the best user experience.`

* [One Identity Authentication Services](https://www.oneidentity.com/products/authentication-services/) version 4.2.x or later

    * `This collection expects the components and structure of Authentication Services 4.2.x or later.`
    * See collection role [documentation](docs/README.md) for specific, per-role  requirements and instructions.
    * See One Identity Authentication Services [documentation](https://support.oneidentity.com/authentication-services/4.2.3/technical-documents) for Authentication Services requirements and instructions.

### From Ansible Galaxy 
The collection will soon be available through [Ansible Galaxy](https://galaxy.ansible.com/) until then please use the [Local Build and Install](###LocalBuildandInstall) instructions. 

To install from [Ansible Galaxy](https://galaxy.ansible.com/) you can use the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command to install the collection on your control node:

```
ansible-galaxy collection install oneidentity.authentication_services
```

By default, the collection is installed in `~/.ansible/collections`.   The installation location can be changed by using the `-p` option with the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command: 

```
ansible-galaxy collection install oneidentity.authentication_services -p /somewhere/collections
```

### Local Build and Install

For local build and installation, you can clone the Git repository, build the collection artifact, and install the locally built collection artifact.  This would be useful for those wishing to extend or customize the collection.

1. Clone the Git repository:

```
git clone https://github.com/OneIdentity/ansible-authentication-services.git
```

2. Run a local build inside the collection using the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command:

```
cd ansible-authentication-services
ansible-galaxy collection build
```

The build command will generate an Ansible Galaxy collection artifact with a `tar.gz` file extension, sample output will look the following:

```
Created collection for oneidentity.authentication_services at /home/user/ansible-authentication-services/oneidentity-authentication_services-0.0.1.tar.gz
```

3. Install the locally built collection artifact using the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command:

```
ansible-galaxy collection install /home/user/ansible-authentication-services/oneidentity-authentication_services-0.0.1.tar.gz
```

By default, the collection is installed in `~/.ansible/collections`.   The installation location can be changed by using the `-p` option with the [ansible-galaxy](https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html) command: 

```
ansible-galaxy collection install /home/user/ansible-authentication-services/oneidentity-authentication_services-0.0.1.tar.gz -p /somewhere/collections
```

## Usage

The collection provides various sample playbooks in the [examples](examples/README.md) directory. 

## Supported Platforms

All Authentication Services supported [platforms](https://support.oneidentity.com/technical-documents/authentication-services/4.2.3/release-notes/2#TOPIC-1376245) except IBM AIX and Amazon Linux AMI.  Support for IBM AIX and Amazon Linux AMI will be added soon.

## Notes

### Known issues

* Check mode does not work as expected for the client_sw role.  No changes are made and it doesn't cause errors but the stated changes that would or would not be made if run normally are not accurate.
* The directory of client software install packages has to be on the Ansible control node.  It would be nice to be able to point to this directory on another machine but this is not possible at this time.
* The IPV4 address for HP-UX machines does not show up in the CSV and HTML reports, this is due to differences in how facts are reported for this OS.  No plan to fix at issue at this time.

### TODO's

* Add support to client_sw role for IBM AIX and Amazon Linux AMI platforms.
* Implement client_join role.
* Implement client_profile role.
* Other roles/features depending on interest may include roles to automate server software deployment, server configuration, and server profiling.
