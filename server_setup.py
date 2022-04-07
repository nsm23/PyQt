import os
import setuptools

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setuptools.setup(
    name='server messenger',
    version='1.0.0',
    packages=['server', 'configs'],
    include_package_data=True,
    author='Sergey',
    author_email='Sergey@mail.ru',
    keywords=['pyqt', 'messenger'],
    install_requires=['PyQt>=5'],
    entry_points={
        'console_scripts': ['run_client=client.run_client:main',
                            'run_server=server.run_server:main']
    }
)


    
