
import os
import sys
import re
import keyring

keyring.set_keyring(keyring.backends.OS_X.Keyring())

def issue_smbfs_mount_command(data):
    if data.get('username', None) is not None:
        auth_prefix = data['username']
        if data.get('password', None) is not None:
            password = data['password']
            auth_prefix = '{0}:{1}'.format(auth_prefix, password)
        auth_prefix = '{0}@'.format(auth_prefix)
    else:
        auth_prefix = ''

    mount_command_template = 'mount -t smbfs //{auth_prefix}{host}/{share}/{path} {mountpoint}'
    kwargs = {}
    kwargs.update(data)
    kwargs['auth_prefix'] = auth_prefix
    mount_command = mount_command_template.format(**kwargs)
    mountpoint = data['mountpoint']
    if not os.path.exists(mountpoint):
        try:
            os.makedirs(mountpoint)
        except OSError:
            basedir = os.path.split(mountpoint)[0]
            raise OSError('Could not create {0}. Try creating {1} manually.'.format(mountpoint, basedir))
    retval = os.system(mount_command)
    return retval


def set_keyring_passwd(username, password):
    keyring.set_password('org.unintuitive.org.smbfs_taskbar','miburr','somepass')

def get_keyring_password(username):
    keyring.get_password('org.unintuitive.org.smbfs_taskbar','miburr')

def interactive_wx_get_password():
    return wx.GetPasswordFromUser(message='Please Enter Your CEC Password', caption='Network Password')

def cleanup_smb_url(string):
    string = re.sub(r'[/]+', '/', string)
    string = '/' + string
    return string
