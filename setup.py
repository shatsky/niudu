from distutils.core import setup
import glob
setup(name='niudu',
      version='0.0.1',
      packages=['niudu_devices', 'niudu_devices.subsystems', 'niudu_devices.plugins'],
      scripts=['niudu-devices'],
      data_files=[('share/niudu-devices/icons', glob.glob('niudu_devices/icons/*')), ('share/niudu-devices/hwdata', glob.glob('niudu_devices/hwdata/*')),
                  ('share/applications', ['niudu-devices.desktop'])
                  ]
      )
