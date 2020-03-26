import os


def get_file_contents(device, filename):
    with open(os.path.join(device, filename), 'r') as f:
        return f.read()[:-1]


def get_symlink_path(device, symlink_name):
    return os.path.realpath(device+'/'+symlink_name)
