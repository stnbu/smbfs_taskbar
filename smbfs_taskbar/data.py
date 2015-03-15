import os
import sqlite3

for dir in os.path.expanduser('~'), os.getenv('HOME', None):
    if dir is None:
        continue
    if os.path.isdir(dir):
        USER_BASE_DIR = os.path.join(dir, '.smbfs_taskbar')
        break
else:
    raise OSError('Cannot find your home directory!')
USER_DB_FILE = os.path.join(USER_BASE_DIR, 'application_data.db')

APPLICATION_TITLE = 'smbfs Mount Manager'

class ApplicationData(object):

    preferences_table_name = 'preferences'
    mounts_table_name = 'mounts'

    def __init__(self, path):
        self.path = path
        self._connection = None

    @property
    def connection(self):
        if self._connection is None:
            dirname = os.path.dirname(self.path)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            self._connection = sqlite3.connect(self.path)
        return self._connection

    def _create_preferences_table(self):
        sql = ('''CREATE TABLE IF NOT EXISTS {table_name}
                        (
                            auto_mount INTEGER,
                            save_passwords INTEGER,
                            default_username TEXT,
                            mount_command TEXT
                        )
                    '''.format(table_name=self.preferences_table_name))
        self.connection.execute(sql)
        cursor = self.connection.execute('SELECT * FROM {table_name};'.format(table_name=self.preferences_table_name))
        if not cursor.fetchall():
            sql = 'INSERT INTO {table_name}\n'.format(table_name=self.preferences_table_name)
            sql += '( auto_mount, save_passwords, default_username, mount_command )\n'
            sql += 'VALUES\n'
            sql += '( 1, 1, "", "")'
            self.connection.execute(sql)
        self.connection.commit()

    def _create_mounts_table(self):
        sql = ('''CREATE TABLE IF NOT EXISTS {table_name}
                        (
                            username TEXT,
                            host TEXT,
                            share TEXT,
                            path TEXT,
                            mountpoint TEXT,
                            PRIMARY KEY (host, share, path)
                        )
                    '''.format(table_name=self.mounts_table_name))
        self.connection.execute(sql)
        self.connection.commit()

    def write(self, preferences=None, mounts=None):
        if preferences is not None:
            values = []
            self._create_preferences_table()
            sql = 'UPDATE {table_name} SET \n'.format(table_name=self.preferences_table_name)
            for field_name, value in preferences.iteritems():
                values.append(value)
                sql += '{field_name} = ?,\n'.format(field_name=field_name, value=value)
            sql = sql.rstrip()
            sql = sql.rstrip(',')
            self.connection.execute(sql, values)
            self.connection.commit()
        if mounts is not None:
            self._create_mounts_table()
            for mount in mounts:
                if not self.get_mount(mount):
                    mount = [(k,v) for k,v in mount.iteritems()]
                    values = [v for k,v in mount]
                    sql = 'INSERT INTO {table_name}\n'.format(table_name=self.mounts_table_name)
                    columns = [c for c,v in mount]
                    columns = ', '.join(columns)
                    sql += '( {columns} )\n'.format(columns=columns)
                    sql += 'VALUES\n'
                    sql += '( {0} )\n'.format(', '.join(['?']*len(mount)))
                else:
                    mount = [(k,v) for k,v in mount.iteritems()]
                    values = [v for k,v in mount]
                    sql = 'UPDATE {table_name} SET \n'.format(table_name=self.mounts_table_name)
                    for field_name, value in mount:
                        sql += '{field_name} = ?,\n'.format(field_name=field_name)
                    sql = sql.rstrip()
                    sql = sql.rstrip(',')
                    sql += '\n'
                    sql += 'WHERE '
                    ands = []
                    for field_name, value in mount:
                        if field_name == 'username':
                            continue
                        values.append(value)
                        ands.append('{field_name} = ?'.format(field_name=field_name))
                    sql += '\n AND '.join(ands)
                self.connection.execute(sql, values)
                self.connection.commit()

    def get_mount(self, mount):
        self._create_mounts_table()
        sql = 'SELECT * from {table_name} \n'.format(table_name=self.mounts_table_name)
        values = []
        if mount is not None:
            sql += ' WHERE '
            ands = []
            for field_name, value in mount.iteritems():
                if field_name == 'username':
                    continue
                values.append(value)
                ands.append('{field_name} = ?'.format(field_name=field_name))
            sql += '\n AND '.join(ands)
        cursor = self.connection.execute(sql, values)
        mounts = cursor.fetchall()
        _mounts = []
        for m in mounts:
            m = zip(('username', 'host', 'share', 'path', 'mountpoint',), m)
            m = dict(m)
            _mounts.append(m)
        if mount is not None:
            try:
                _mounts, = _mounts
            except ValueError:
                _mounts = None
        return _mounts

    def get_mounts(self):
        return self.get_mount(mount=None)

    def get_preferences(self):
        def get():
            sql = 'SELECT * from {table_name} ;\n'.format(table_name=self.preferences_table_name)
            cursor = self.connection.execute(sql)
            return cursor.fetchall()
        self._create_preferences_table()
        preferences = get()
        if len(preferences) == 0:
            self.write(preferences={
                'auto_mount': '1',
                'save_passwords': '1',
                'default_username': '',
                'mount_command': 'mount',
            })
            preferences = get()
        assert len(preferences) == 1, "Did not get exactly one preferences record."
        preferences, = preferences
        preferences = zip(('auto_mount', 'save_passwords', 'default_username', 'mount_command'), preferences)
        preferences = dict(preferences)
        return preferences
