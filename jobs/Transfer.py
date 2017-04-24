# pylint: disable=C0103
# pylint: disable=C0111
# pylint: disable=C0301
import os
import sys
import json
import time
import logging
import paramiko

from pprint import pformat
from datetime import datetime, timedelta
from uuid import uuid4

from paramiko import PasswordRequiredException
from paramiko import SSHException

from globusonline.transfer import api_client
from globusonline.transfer.api_client import Transfer as globus_transfer
from globusonline.transfer.api_client import TransferAPIClient
from globusonline.transfer.api_client import TransferAPIError
from globusonline.transfer.api_client import x509_proxy
from globusonline.transfer.api_client.goauth import get_access_token
from globusonline.transfer.api_client.goauth import GOCredentialsError

from lib.util import print_debug
from lib.util import print_message
from lib.util import filename_to_year_set
from lib.util import format_debug
from lib.util import push_event
from lib.util import raw_file_cmp
from JobStatus import JobStatus

class Transfer(object):
    """
    Uses Globus to transfer files between DTNs
    """
    def __init__(self, config=None, event_list=None):
        self.event_list = event_list
        self.config = {}
        self.status = JobStatus.INVALID
        self.type = 'transfer'
        self.outputs = {
            "status": self.status
        }
        self.uuid = uuid4().hex
        self.inputs = {
            'file_list': '',
            'recursive': '',
            'globus_username': '',
            'globus_password': '',
            'source_endpoint': '',
            'destination_endpoint': '',
            'source_username': '',
            'source_password': '',
            'destination_username': '',
            'destination_password': '',
            'source_path': '',
            'destination_path': '',
            'pattern': '',
        }
        self.maximum_transfers = 12
        self.prevalidate(config)
        self.msg = None
        self.job_id = 0

    def save(self, conf_path):
        """
        Saves job configuration to a json file at conf_path
        """
        try:
            with open(conf_path, 'r') as infile:
                config = json.load(infile)
            with open(conf_path, 'w') as outfile:
                config[self.uuid]['inputs'] = self.config
                config[self.uuid]['outputs'] = self.outputs
                config[self.uuid]['type'] = self.type
                json.dump(config, outfile, indent=4)
        except Exception as e:
            print_message('Error saving configuration file')
            print_debug(e)
            raise

    def get_type(self):
        """
        Returns job type
        """
        return self.type

    def get_file_list(self):
        return self.inputs.get('file_list')

    def __str__(self):
        return pformat({
            'config': self.config,
            'status': self.status
        }, indent=4)

    def prevalidate(self, config=None):
        """
        Validates transfer inputs
        """
        if self.status == JobStatus.VALID:
            return 0
        for i in config:
            if i in self.inputs:
                if i == 'recursive':
                    if config.get(i) == 'True':
                        self.config[i] = True
                    else:
                        self.config[i] = False
                else:
                    self.config[i] = config.get(i)

        for i in self.inputs:
            if i not in self.config or self.config[i] == None:
                if i == 'file_list':
                    self.config[i] = ''
                elif i == 'recursive':
                    self.config[i] = False
                else:
                    print_message('Missing transfer argument {}'.format(i))
                    self.status = JobStatus.INVALID
                    return -1
        self.status = JobStatus.VALID
        # only add the first n transfers up to the max
        file_list = sorted(self.config.get('file_list'), raw_file_cmp)
        self.config['file_list'] = file_list[:self.maximum_transfers]

        for file_info in file_list:
            destination = os.path.join(self.config.get('destination_path'), file_info['type'])
            if not os.path.exists(destination):
                os.makedirs(destination)
        return 0

    def postvalidate(self):
        print 'transfer postvalidate'

    def activate_endpoint(self, api_client, endpoint, username, password):
        code, reason, result = api_client.endpoint_autoactivate(endpoint, if_expires_in=2880)
        if result["code"] == "AutoActivationFailed":
            reqs = result
            myproxy_hostname = None
            for r in result['DATA']:
                if r['type'] == 'myproxy' and r['name'] == 'hostname':
                    myproxy_hostname = r['value']
            reqs.set_requirement_value("myproxy", "hostname", myproxy_hostname)
            reqs.set_requirement_value("myproxy", "username", username)
            reqs.set_requirement_value("myproxy", "passphrase", password)
            reqs.set_requirement_value("myproxy", "lifetime_in_hours", "168")
            try:
                code, reason, result = api_client.endpoint_activate(endpoint, reqs)
            except:
                raise
            if code != 200:
                logging.error("Could not activate the endpoint: %s. Error: %s - %s", endpoint, result["code"], result["message"])

    def get_destination_path(self, srcpath, dstpath, recursive):
        '''
        If destination path is a directory (ends with '/') adds source file name to the destination path.
        Otherwise, Globus will treat the destination path as a file in spite of the fact that it is a directory.
        '''
        if srcpath:
            if not recursive:
                if dstpath.endswith('/'):
                    basename = os.path.basename(srcpath)
                    return dstpath + basename
        return dstpath

    def display_status(self, event_list, percent_complete, task_id):
        """
        Updates the event_list with a nicely formated percent completion
        """
        start_file = self.config.get('file_list')[0]
        end_file = self.config.get('file_list')[-1]
        if not 'mpas-' in start_file:
            index = start_file['filename'].find('-')
            start_file = start_file['filename'][index - 4: index + 3]
        if not 'mpas-' in end_file:
            index = end_file['filename'].find('-')
            end_file = end_file['filename'][index - 4: index + 3]

        start_end_str = '{start} to {end}'.format(
            start=start_file,
            end=end_file)
        message = 'Transfer {0} in progress ['.format(start_end_str)
        for i in range(1, 100, 5):
            if i < percent_complete:
                message += '*'
            else:
                message += '_'
        message += '] {0:.2f}%'.format(percent_complete)
        replaced = False
        for i, e in enumerate(event_list):
            if start_end_str in e:
                event_list[i] = time.strftime("%I:%M") + ' ' + message
                replaced = True
                break
        if not replaced:
            event_list = push_event(event_list, message)

    def error_cleanup(self):
        print_message('Removing partially transfered files')
        destination_contents = os.listdir(self.config.get('destination_path'))
        for transfer in self.config['file_list']:
            t_file = transfer['filename'].split(os.sep)[-1]
            if t_file in destination_contents:
                os.remove(os.path.join(self.config.get('destination_path'), t_file))

    def execute(self, event, event_list):
        # reject if job isnt valid
        if self.status != JobStatus.VALID:
            logging.error('Transfer job in invalid state')
            logging.error(str(self))
            return

        # Get source and destination UUIDs
        srcendpoint = self.config.get('source_endpoint')
        dstendpoint = self.config.get('destination_endpoint')
        message = 'Starting transfer job from {src} to {dst}'.format(
            src=srcendpoint,
            dst=dstendpoint)
        logging.info(message)
        # event_list = push_event(event_list, message)
        # Get access token (This method of getting an acces token is deprecated and should be replaced by OAuth2 calls).
        globus_username = self.config.get('globus_username')
        globus_password = self.config.get('globus_password')
        try:
            auth_result = get_access_token(globus_username, globus_password)
        except GOCredentialsError as e:
            msg = 'Invalid globus credentials, failed starting file transfer'
            event_list = push_event(event_list, msg)
            self.status = JobStatus.FAILED
            return

        # Create a transfer submission
        successful_activation = False
        for i in range(5):
            try:
                api_client = TransferAPIClient(globus_username, goauth=auth_result.token)
            except:
                continue
            source_user = self.config.get('source_username')
            source_pass = self.config.get('source_password')
            try:
                self.activate_endpoint(api_client, srcendpoint, source_user, source_pass)
            except Exception as e:
                logging.error('Error activating source endpoing, attempt %s', int(i) + 1)
                logging.error(format_debug(e))
            else:
                successful_activation = True
                break
        if not successful_activation:
            msg = 'Unable to activate source endpoint after five attempts, exiting'
            logging.error(msg)
            self.event_list(msg)
            self.status = JobStatus.FAILED
            return

        successful_activation = False
        for i in range(5):
            dst_user = self.config.get('destination_username')
            dst_pass = self.config.get('destination_password')
            try:
                self.activate_endpoint(api_client, dstendpoint, dst_user, dst_pass)
            except Exception as e:
                logging.error('Error activating destination endpoing, attempt %s', int(i) + 1)
                logging.error(format_debug(e))
            else:
                successful_activation = True
                break
        if not successful_activation:
            msg = 'Unable to activate destination endpoint after five attempts, exiting'
            logging.error(msg)
            self.event_list(msg)
            self.status = JobStatus.FAILED
            return

        try:
            code, message, data = api_client.transfer_submission_id()
            submission_id = data["value"]
            deadline = datetime.utcnow() + timedelta(days=10)
            transfer_task = globus_transfer(submission_id, srcendpoint, dstendpoint, deadline)
        except Exception as e:
            logging.error('Error creating transfer task')
            logging.error(format_debug(e))
            self.status = JobStatus.FAILED
            return

        if not self.config['file_list']:
            logging.error('Unable to transfer files without a source list')
            self.status = JobStatus.FAILED
            return
        try:
            for path in self.config['file_list']:
                dst_path = os.path.join(
                    self.config.get('destination_path'),
                    path['type'],
                    path['filename'].split('/')[-1])
                transfer_task.add_item(
                    path['filename'],
                    dst_path,
                    recursive=self.config.get('recursive'))
        except IOError as e:
            logging.error('Error opening source list')
            logging.error(format_debug(e))
            self.status = JobStatus.FAILED
            return

        # Start the transfer
        task_id = None
        try:
            code, reason, data = api_client.transfer(transfer_task)
            task_id = data["task_id"]
            logging.info('starting transfer with task id %s', task_id)
            code, reason, data = api_client.task(task_id)
        except Exception as e:
            logging.error("Could not submit the transfer")
            logging.error(format_debug(e))
            self.status = 'error'
            return

        # Check a status of the transfer every minute (60 secs)
        number_transfered = -1
        while True:
            try:
                while True:
                    try:
                        code, reason, data = api_client.task(task_id)
                    except:
                        time.sleep(1)
                    else:
                        break
                if data['status'] == 'SUCCEEDED':
                    logging.info('progress %d/%d', data['files_transferred'], data['files'])
                    percent_complete = 100.0
                    self.display_status(event_list, percent_complete, task_id)
                    message = 'Transfer job completed'
                    self.status = JobStatus.COMPLETED
                    return ('success', '')
                elif data['status'] == 'FAILED':
                    logging.error('Error transfering files %s', data.get('nice_status_details'))
                    self.status = JobStatus.FAILED
                    return ('error', data['nice_status_details'])
                elif data['status'] == 'ACTIVE':
                    if number_transfered < data['files_transferred']:
                        number_transfered = data['files_transferred']
                        logging.info('progress %d/%d', data['files_transferred'], data['files'])
                        percent_complete = (float(data['files_transferred']) / float(data['files'])) * 100
                        self.display_status(event_list, percent_complete, task_id)

                    self.status = JobStatus.RUNNING
                if event and event.is_set():
                    api_client.task_cancel(task_id)
                    self.error_cleanup()
                    return
            except Exception as e:
                if code:
                    print code, reason
                logging.error(format_debug(e))
                api_client.task_cancel(task_id)
                self.error_cleanup()
                return
            time.sleep(5)
