from kivy.logger import Logger
import os
import paramiko
import vyattaconfparser
import json


class Router(object):
    def __init__(self, config, resp_q):
        self.commands = {
            'connect': self.connect,
            'disconnect': self.disconnect,
            'drop_kids_packets': self.drop_kids_packets,
            'drop_tv_packets': self.drop_tv_packets,
            'allow_kids_packets': self.allow_kids_packets,
            'allow_tv_packets': self.allow_tv_packets,
            'show_firewall': self.show_firewall
        }
        try:
            self.key_file = config['key_file']
            self.ip = config['ip']
            self.user = config['user']
            self.q = resp_q
        except Exception as e:
            raise('Router:exception {e}'.format(e=e))
        Logger.info(
            f'Router: Initializing router data at {self.ip} with user {self.user}' \
                f' key {self.key_file} and response queue {self.q}')

    def do_seq(self, command_seq):
        for command in command_seq:
            print(command)
            self.commands[command]()

    def connect(self):
        response = {'command': 'connect'}
        if not os.access(self.key_file, os.F_OK):
            Logger.error('Router: ssh key file not found')
            response['status'] = 'Failure'
            response['message'] = 'SSH key file not found'
        else:
            try:
                key = paramiko.RSAKey.from_private_key_file(self.key_file)
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(hostname=self.ip, username=self.user, pkey=key, timeout=2)
                response['status'] = 'Success'
                response['message'] = 'OK'
            except Exception as e:
                response['status'] = 'Failure'
                response['message'] = str(e)
        self.q.put(response)
        Logger.info(f'Router: {str(response)}')


    def disconnect(self):
        response = {'command': 'disconnect'}
        try:
            self.client.close()
            response['status'] = 'Success'
            response['message'] = 'OK'
        except Exception as e:
            response['status'] = 'Failure'
            response['message'] = str(e)
        self.q.put(response)
        Logger.info(f'Router: {str(response)}')

    def show_firewall(self):
        response = {'command': 'show_firewall'}
        # stdin, stdout, stderr = self.client.exec_command(
        #    '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper show firewall')
        stdin, stdout, stderr = self.client.exec_command('cat /config/config.boot')
        err = stderr.read().decode()
        if err is '':
            try:
                result = str(stdout.read().decode())
                result = (vyattaconfparser.parse_conf(result))
                # Uncomment to print pretty json
                # print(json.dumps(result, indent=2))

                response['status'] = 'Success'
                response['message'] = {}
                if 'disable' in result['firewall']['name']['WAN_IN']['rule']['10'].keys():
                    response['message']['kids'] = 'enabled'
                else:
                    response['message']['kids'] = 'disabled'
                if 'disable' in result['firewall']['name']['WAN_IN']['rule']['20'].keys():
                    response['message']['tv'] = 'enabled'
                else:
                    response['message']['tv'] = 'disabled'
            except Exception as e:
                response['status'] = 'Failure'
                response['message'] = str(e)
        else:
            response['status'] = 'Failure'
            response['message'] = err

        self.q.put(response)
        Logger.info(f'Router: {response}')

    def drop_kids_packets(self):
        response = {'command': 'drop_kids_packets'}
        stdin, stdout, stderr = self.client.exec_command(
            '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper begin')
        err = stderr.read().decode()
        if err is '':
            stdin, stdout, stderr = self.client.exec_command(
               '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper delete firewall name WAN_IN rule 10 disable')
            err = stderr.read().decode()
            if err is '':
                stdin, stdout, stderr = self.client.exec_command(
                    '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper commit')
                err = stderr.read().decode()
                if err is '':
                    stdin, stdout, stderr = self.client.exec_command(
                        '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper save')
                    err = stderr.read().decode()
                    if err is '':
                        response['status'] = 'Success'
                        response['message'] = 'OK'
                        self.q.put(response)
                        Logger.info(f'Router: {str(response)}')
                        return

        response['status'] = 'Failure'
        response['message'] = err
        self.q.put(response)
        Logger.info(f'Router: {str(response)}')


    def allow_kids_packets(self):
        response = {'command': 'allow_kids_packets'}
        stdin, stdout, stderr = self.client.exec_command(
            '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper begin')
        err = stderr.read().decode()
        if err is '':
            stdin, stdout, stderr = self.client.exec_command(
                '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper set firewall name WAN_IN rule 10 disable')
            err = stderr.read().decode()
            if err is '':
                stdin, stdout, stderr = self.client.exec_command(
                    '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper commit')
                err = stderr.read().decode()
                if err is '':
                    stdin, stdout, stderr = self.client.exec_command(
                        '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper save')
                    err = stderr.read().decode()
                    if err is '':
                        response['status'] = 'Success'
                        response['message'] = 'OK'
                        self.q.put(response)
                        Logger.info(f'Router: {str(response)}')
                        return

        response['status'] = 'Failure'
        response['message'] = err
        self.q.put(response)
        Logger.info(f'Router: {str(response)}')

    def drop_tv_packets(self):
        response = {'command': 'drop_tv_packets'}
        stdin, stdout, stderr = self.client.exec_command(
            '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper begin')
        err = stderr.read().decode()
        if err is '':
            stdin, stdout, stderr = self.client.exec_command(
               '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper delete firewall name WAN_IN rule 20 disable')
            err = stderr.read().decode()
            if err is '':
                stdin, stdout, stderr = self.client.exec_command(
                    '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper commit')
                err = stderr.read().decode()
                if err is '':
                    stdin, stdout, stderr = self.client.exec_command(
                        '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper save')
                    err = stderr.read().decode()
                    if err is '':
                        response['status'] = 'Success'
                        response['message'] = 'OK'
                        self.q.put(response)
                        Logger.info(f'Router: {str(response)}')
                        return

        response['status'] = 'Failure'
        response['message'] = err
        self.q.put(response)
        Logger.info(f'Router: {str(response)}')


    def allow_tv_packets(self):
        response = {'command': 'allow_tv_packets'}
        stdin, stdout, stderr = self.client.exec_command(
            '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper begin')
        err = stderr.read().decode()
        if err is '':
            stdin, stdout, stderr = self.client.exec_command(
                '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper set firewall name WAN_IN rule 20 disable')
            err = stderr.read().decode()
            if err is '':
                stdin, stdout, stderr = self.client.exec_command(
                    '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper commit')
                err = stderr.read().decode()
                if err is '':
                    stdin, stdout, stderr = self.client.exec_command(
                        '/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper save')
                    err = stderr.read().decode()
                    if err is '':
                        response['status'] = 'Success'
                        response['message'] = 'OK'
                        self.q.put(response)
                        Logger.info(f'Router: {str(response)}')
                        return

        response['status'] = 'Failure'
        response['message'] = err
        self.q.put(response)
        Logger.info(f'Router: {str(response)}')
