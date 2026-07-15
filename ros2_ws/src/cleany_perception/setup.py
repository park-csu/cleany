from setuptools import find_packages, setup

package_name = 'cleany_perception'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='이정현',
    maintainer_email='sw292ljh@gmail.com',
    description='Perception node for the Cleany robot: turns camera images into object detection candidates.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # detection_node is registered in a later step once its main() is implemented.
        ],
    },
)
