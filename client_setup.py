import os
import setuptools

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name='clint messenger',
    version='1.0.0',
    packages=['client', 'configs'],
    include_package_data=True,
    author='Sergey',
    author_email='Sergey@mail.ru',
    keywords=['pyqt', 'messenger'],
    install_requires=['required'],
    entry_points={
        'console_scripts': ['run_client=client.run_client:main',
                            'run_server=server.run_server:main']
    }

)


    
