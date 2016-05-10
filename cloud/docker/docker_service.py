# /usr/local/bin/python
#
# Copyright 2016 Red Hat | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''

module: docker_service

short_description: Manage docker services and containers.

version_added: "2.1"

author: "Chris Houseknecht (@chouseknecht)"

description:
  - Consumes docker compose to start, shutdown and scale services.
  - Works with compose versions 1 and 2.
  - Compose can be read from a docker-compose.yml (or .yaml) file or inline using the C(definition) option.
  - See the examples for more details.
  - Supports check mode and differences.

options:
  project_src:
      description:
        - Path to a directory containing a docker-compose.yml or docker-compose.yaml file.
        - Mutually exclusive with C(definition).
        - Required when no C(definition) is provided.
      type: path
      required: false
  project_name:
      description:
        - Provide a project name. If not provided, the project name is taken from the basename of C(project_src).
        - Required when no C(definition) is provided.
      type: str
      required: false
  files:
      description:
        - List of file names relative to C(project_src). Overrides docker-compose.yml or docker-compose.yaml.
        - Files are loaded and merged in the order given.
      type: list
      required: false
  state:
      description:
        - Desired state of the project.
        - Specifying I(present) is the same as running I(docker-compose up).
        - Specifying I(absent) is the same as running I(docker-compose down).
      choices:
        - absent
        - present
      default: present
      type: str
      required: false
  services:
      description:
        - When C(state) is I(present) run I(docker-compose up) on a subset of services.
      type: list
      required: false
  scale:
      description:
        - When C(sate) is I(present) scale services. Provide a dictionary of key/value pairs where the key
          is the name of the service and the value is an integer count for the number of containers.
      type: complex
      required: false
  dependencies:
      description:
        - When C(state) is I(present) specify whether or not to include linked services.
      type: bool
      required: false
      default: true
  definition:
      description:
        - Provide docker-compose yaml describing one or more services, networks and volumes.
        - Mutually exclusive with project_src and project_files
      type: complex
      required: false
  hostname_check:
      description:
        - Whether or not to check the Docker daemon's hostname against the name provided in the client certificate.
      type: bool
      required: false
      default: false
  recreate:
      description:
        - Whether or not to recreate containers whose configuration has driftd from the service definition.
      type: bool
      required: false
      default: true
  build:
      description:
        - Whether or not to build images before starting containers.
        - Missing images will always be built.
        - If an image is present and C(build) is false, the image will not be built.
        - If an image is present and C(build) is true, the image will be built.
      type: bool
      required: false
      default: true
  force_recreate:
      description:
        - Use with state I(present) to always recreate containers, even when they exist and there is no configuration
          drift.
      type: bool
      required: false
      default: false
  remove_images:
      description:
        - Use with state I(absent) to remove the all images or only local images.
      type: str
      required: false
      default: null
  remove_volumes:
      description:
        - Use with state I(absent) to remove data volumes.
      required: false
      type: bool
      default: false
  stopped:
      description:
        - Use with state I(present) to leave the containers in an exited or non-running state.
      required: false
      type: bool
      default: false
  restarted:
      description:
        - Use with state I(present) to restart all containers.
      required: false
      type: bool
      default: false
'''

EXAMPLES = '''
# Examples use the django example at U(https://docs.docker.com/compose/django/). Follow it to create the flask
# directory

- name: Run using a project directory
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - docker_service:
        project_src: flask
        state: absent

    - docker_service:
        project_src: flask
      register: output

    - debug: var=output

    - docker_service:
        project_src: flask
        build: no
      register: output

    - debug: var=output

    - assert:
        that: "not output.changed "

    - docker_service:
        project_src: flask
        build: no
        stopped: true
      register: output

    - debug: var=output

    - assert:
        that:
          - "not web.flask_web_1.state.running"
          - "not db.flask_db_1.state.running"

    - docker_service:
        project_src: flask
        build: no
        restarted: true
      register: output

    - debug: var=output

    - assert:
        that:
          - "web.flask_web_1.state.running"
          - "db.flask_db_1.state.running"

- name: Scale the web service to 2
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - docker_service:
        project_src: flask
        scale:
          web: 2
      register: output

    - debug: var=output

- name: Run with inline v2 compose
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - docker_service:
        project_src: flask
        state: absent

    - docker_service:
        project_name: flask
        definition:
          version: '2'
          services:
            db:
              image: postgres
            web:
              build: "{{ playbook_dir }}/flask"
              command: "python manage.py runserver 0.0.0.0:8000"
              volumes:
                - "{{ playbook_dir }}/flask:/code"
              ports:
                - "8000:8000"
              depends_on:
                - db
      register: output

    - debug: var=output

    - assert:
        that:
          - "web.flask_web_1.state.running"
          - "db.flask_db_1.state.running"

- name: Run with inline v1 compose
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - docker_service:
        project_src: flask
        state: absent

    - docker_service:
        project_name: flask
        definition:
            db:
              image: postgres
            web:
              build: "{{ playbook_dir }}/flask"
              command: "python manage.py runserver 0.0.0.0:8000"
              volumes:
                - "{{ playbook_dir }}/flask:/code"
              ports:
                - "8000:8000"
              links:
                - db
      register: output

    - debug: var=output

    - assert:
        that:
          - "web.flask_web_1.state.running"
          - "db.flask_db_1.state.running"
'''

RETURN = '''
service:
  description: Name of the service.
  returned: success
  type: complex
  contains:
      container_name:
          description: Name of the container. Format is I(project_service_#).
          returned: success
          type: complex
          contains:
              cmd:
                  description: One or more commands to be executed in the container.
                  returned: success
                  type: list
                  example: ["postgres"]
              image:
                  description: Name of the image from which the container was built.
                  returned: success
                  type: str
                  example: postgres
              labels:
                  description: Meta data assigned to the container.
                  returned: success
                  type: complex
                  example: {...}
              networks:
                  description: Contains a dictionary for each network to which the container is a member.
                  returned: success
                  type: complex
                  contains:
                      IPAddress:
                          description: The IP address assigned to the container.
                          returned: success
                          type: string
                          example: 172.17.0.2
                      IPPrefixLen:
                          description: Number of bits used by the subnet.
                          returned: success
                          type: int
                          example: 16
                      aliases:
                          description: Aliases assigned to the container by the network.
                          returned: success
                          type: list
                          example: ['db']
                      globalIPv6:
                          description: IPv6 address assigned to the container.
                          returned: success
                          type: str
                          example: ''
                      globalIPv6PrefixLen:
                          description: IPv6 subnet length.
                          returned: success
                          type: int
                          example: 0
                      links:
                          description: List of container names to which this container is linked.
                          returned: success
                          type: list
                          example: null
                      macAddress:
                          description: Mac Address assigned to the virtual NIC.
                          returned: success
                          type: str
                          example: "02:42:ac:11:00:02"
              state:
                  description: Information regarding the current disposition of the container.
                  returned: success
                  type: complex
                  contains:
                      running:
                          description: Whether or not the container is up with a running process.
                          returned: success
                          type: bool
                          example: true
                      status:
                          description: Description of the running state.
                          returned: success
                          type: str
                          example: running
'''

HAS_COMPOSE = True
HAS_COMPOSE_EXC = None

import yaml

from ansible.module_utils.basic import *

try:
    from compose.cli.command import project_from_options
    from compose.service import ConvergenceStrategy
    from compose.cli.main import convergence_strategy_from_opts, build_action_from_opts, image_type_from_opt
except ImportError as exc:
    HAS_COMPOSE = False
    HAS_COMPOSE_EXC = six.__file__

from ansible.module_utils.docker_common import *


AUTH_PARAM_MAPPING = {
    u'docker_host': u'--host',
    u'tls': u'--tls',
    u'cacert_path': u'--tlscacert',
    u'cert_path': u'--tlscert',
    u'key_path': u'--tlskey',
    u'tls_verify': u'--tlsverify'
}


class ContainerManager(DockerBaseClass):

    def __init__(self, client):

        super(ContainerManager, self).__init__(module=client.module)

        self.client = client
        self.project_src = None
        self.project_files = None
        self.project_name = None
        self.state = None
        self.definition = None
        self.hostname_check = None
        self.timeout = None
        self.force_recreate = None
        self.remove_images = None
        self.remove_orphans = None
        self.remove_volumes = None
        self.stopped = None
        self.restarted = None
        self.recreate = None
        self.build = None
        self.dependencies = None
        self.services = None
        self.scale = None

        self.check_mode = client.check_mode
        self.diff = client.module._diff

        for key, value in client.module.params.items():
            setattr(self, key, value)

        self.options = dict()
        self.options.update(self._get_auth_options())
        self.options[u'--skip-hostname-check'] = (not self.hostname_check)

        if self.project_name:
            self.options[u'--project-name'] = self.project_name

        if self.project_files:
            self.options[u'--file'] = self.project_files

        if not HAS_COMPOSE:
            self.fail("Unable to load docker-compose. Try `pip install docker-compose`. Error: %s" % HAS_COMPOSE_EXC)

        self.log("options: ")
        self.log(self.options, pretty_print=True)

        if self.definition:
            if not self.project_name:
                self.fail("Parameter error - project_name required when providing definition.")

            self.project_src = tempfile.mkdtemp(prefix="ansible")
            compose_file = os.path.join(self.project_src, "docker-compose.yml")
            try:
                self.log('writing: ')
                self.log(yaml.dump(self.definition, default_flow_style=False))
                with open(compose_file, 'w') as f:
                    f.write(yaml.dump(self.definition, default_flow_style=False))
            except Exception as exc:
                self.fail("Error writing to %s - %s" % (compose_file, str(exc)))
        else:
            if not self.project_src:
                self.fail("Parameter error - project_src required.")

        try:
            self.log("project_src: %s" % self.project_src)
            self.project = project_from_options(self.project_src, self.options)
        except Exception as exc:
            self.fail("Configuration error - %s" % str(exc))

    def fail(self, msg):
        self.client.fail(msg)

    def exec_module(self):
        result = None

        if self.state == 'present':
            result = self.cmd_up()
        elif self.state == 'absent':
            result = self.cmd_down()

        if self.definition:
            compose_file = os.path.join(self.project_src, "docker-compose.yml")
            self.log("removing %s" % compose_file)
            os.remove(compose_file)
            self.log("removing %s" % self.project_src)
            os.rmdir(self.project_src)

        return result

    def _get_auth_options(self):
        options = dict()
        for key, value in self.client.auth_params.items():
            if value is not None:
                option = AUTH_PARAM_MAPPING.get(key)
                if option:
                    options[option] = value
        return options

    def cmd_up(self):

        start_deps = self.dependencies
        service_names = self.services
        detached = True
        result = dict(changed=False, diff=dict(), ansible_facts=dict())

        up_options = {
            u'--no-recreate': not self.recreate,
            u'--build': self.build,
            u'--no-build': False,
            u'--no-deps': False,
        }

        if self.force_recreate:
            up_options[u'--no-recreate'] = False

        up_options[u'--force-recreate'] = self.force_recreate

        if self.remove_orphans:
            up_options[u'--remove-orphans'] = True

        for service in self.project.services:
            if not service_names or service.name in service_names:
                plan = service.convergence_plan(strategy=convergence_strategy_from_opts(up_options))
                if plan.action != 'noop':
                    result['changed'] = True
                if self.diff:
                    result['diff'][service.name] = dict()
                    result['diff'][service.name][plan.action] = []
                    for container in plan.containers:
                        result['diff'][service.name][plan.action].append(dict(
                            id=container.id,
                            name=container.name,
                            short_id=container.short_id,
                        ))

        if not self.check_mode and result['changed']:
            try:
                self.project.up(
                    service_names=service_names,
                    start_deps=start_deps,
                    strategy=convergence_strategy_from_opts(up_options),
                    do_build=build_action_from_opts(up_options),
                    detached=detached,
                    remove_orphans=self.remove_orphans)
            except Exception as exc:
                self.fail("Error bring %s up - %s" % (self.project.name, str(exc)))

        if self.stopped:
            result.update(self.cmd_stop(service_names))

        if self.restarted:
            result.update(self.cmd_restart(service_names))

        if self.scale:
            result.update(self.cmd_scale())

        for service in self.project.services:
            result['ansible_facts'][service.name] = dict()
            for container in service.containers(stopped=True):
                inspection = container.inspect()
                # pare down the inspection data to the most useful bits
                facts = dict()
                facts['cmd'] = inspection['Config']['Cmd']
                facts['labels'] = inspection['Config']['Labels']
                facts['image'] = inspection['Config']['Image']
                facts['state'] = dict(
                    running=inspection['State']['Running'],
                    status=inspection['State']['Status'],
                )
                facts['networks'] = dict()
                for key, value in inspection['NetworkSettings']['Networks'].items():
                    facts['networks'][key] = dict(
                        aliases=inspection['NetworkSettings']['Networks'][key]['Aliases'],
                        globalIPv6=inspection['NetworkSettings']['Networks'][key]['GlobalIPv6Address'],
                        globalIPv6PrefixLen=inspection['NetworkSettings']['Networks'][key]['GlobalIPv6PrefixLen'],
                        IPAddress=inspection['NetworkSettings']['Networks'][key]['IPAddress'],
                        IPPrefixLen=inspection['NetworkSettings']['Networks'][key]['IPPrefixLen'],
                        links=inspection['NetworkSettings']['Networks'][key]['Links'],
                        macAddress=inspection['NetworkSettings']['Networks'][key]['MacAddress'],
                    )
                result['ansible_facts'][service.name][container.name] = facts

        return result

    def cmd_down(self):
        result = dict(
            changed=False,
            diff=dict(),
        )

        for service in self.project.services:
            containers = service.containers(stopped=True)
            if len(containers):
                result['changed'] = True
            if self.diff:
                result['diff'][service.name] = dict()
                result['diff'][service.name]['deleted'] = [container.name for container in containers]

        if not self.check_mode and result['changed']:
            image_type = image_type_from_opt('--rmi', self.remove_images)
            try:
                self.project.down(image_type, self.remove_volumes, self.remove_orphans)
            except Exception as exc:
                self.fail("Error bringing %s down - %s" % (self.project.name, str(exc)))

        return result

    def cmd_stop(self, service_names):
        result = dict(
            changed=False,
            diff=dict()
        )
        for service in self.project.services:
            if not service_names or service.name in service_names:
                result['diff'][service.name] = dict()
                result['diff'][service.name]['stop'] = []
                for container in service.containers(stopped=False):
                    result['changed'] = True
                    if self.diff:
                        result['diff'][service.name]['stop'].append(dict(
                            id=container.id,
                            name=container.name,
                            short_id=container.short_id,
                        ))

        if not self.check_mode and result['changed']:
            try:
                self.project.stop(service_names=service_names)
            except Exception as exc:
                self.fail("Error stopping services for %s - %s" % (self.project.name, str(exc)))

        return result

    def cmd_restart(self, service_names):
        result = dict(
            changed=False,
            diff=dict()
        )

        for service in self.project.services:
            if not service_names or service.name in service_names:
                result['diff'][service.name] = dict()
                result['diff'][service.name]['restart'] = []
                for container in service.containers(stopped=True):
                    result['changed'] = True
                    if self.diff:
                        result['diff'][service.name]['restart'].append(dict(
                            id=container.id,
                            name=container.name,
                            short_id=container.short_id,
                        ))

        if not self.check_mode and result['changed']:
            try:
                self.project.restart(service_names=service_names)
            except Exception as exc:
                self.fail("Error restarting services for %s - %s" % (self.project.name, str(exc)))

        return result

    def cmd_scale(self):
        result = dict(
            changed=False,
            diff=dict()
        )

        for service in self.project.services:
            if service.name in self.scale:
                result['diff'][service.name] = dict()
                containers = service.containers(stopped=True)
                if len(containers) != self.scale[service.name]:
                    result['changed'] = True
                    if self.diff:
                        result['diff'][service.name]['scale'] = self.scale[service.name] - len(containers)
                    if not self.check_mode:
                        try:
                            service.scale(self.scale[service.name])
                        except Exception as exc:
                            self.fail("Error scaling %s - %s" % (service.name, str(exc)))
        return result


def main():
    argument_spec = dict(
        project_src=dict(type='path'),
        project_name=dict(type='str',),
        files=dict(type='list'),
        state=dict(type='str', choices=['absent', 'present'], default='present'),
        definition=dict(type='dict'),
        hostname_check=dict(type='bool', default=False),
        recreate=dict(type='bool', default=True),
        build=dict(type='bool', default=True),
        force_recreate=dict(type='bool', default=False),
        remove_images=dict(type='str', choices=['all', 'local']),
        remove_volumes=dict(type='bool', default=False),
        remove_orphans=dict(type='bool', default=False),
        stopped=dict(type='bool', default=False),
        restarted=dict(type='bool', default=False),
        scale=dict(type='dict'),
        services=dict(type='list'),
        dependencies=dict(type='bool', default=True)
    )

    mutually_exclusive = [
        ('force_recreate', 'no_recreate'),
        ('definition', 'project_src'),
        ('definition', 'files')
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True
    )

    result = ContainerManager(client).exec_module()
    client.module.exit_json(**result)


if __name__ == '__main__':
    main()
