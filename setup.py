from setuptools import setup

requirements = [
    'pyqt5-sip',
    'PyQt5',
    'PyYAML==5.1',
    'schedule==0.6.0'
]

test_requirements = [
    'pytest',
    'pytest-cov',
    'pytest-faulthandler',
    'pytest-mock',
    'pytest-qt',
    'pytest-xvfb',
]

setup(
    name='frame',
    version='0.0.1',
    description="A PyQt5 GUI application",
    author="scott carver",
    author_email='scott@artificia.org',
    url='https://github.com/scztt/frame',
    packages=['frame', 'frame.images',
              'frame.tests'],
    package_data={'frame.images': ['*.png']},
    entry_points={
        'console_scripts': [
            'frame=frame.frame:main'
        ]
    },
    install_requires=requirements,
    zip_safe=False,
    keywords='frame',
    classifiers=[
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
