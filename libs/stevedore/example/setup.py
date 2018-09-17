from setuptools import setup, find_packages

setup(
    name='stevedore-examples',
    version='1.0',

    description='Demonstration package for stevedore',

    author='Doug Hellmann',
    author_email='doug@doughellmann.com',

    url='http://git.openstack.org/cgit/openstack/stevedore',

    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=['stevedore.examples',
              ],

    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'stevedore.example.formatter': [
            'simple = stevedore.example.simple:Simple',
            'plain = stevedore.example.simple:Simple',
        ],
    },

    zip_safe=False,
)
