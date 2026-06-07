# setup.py - For pip install
from setuptools import setup, find_packages

setup(
    name="vaultkeeper",
    version="3.1.0",
    description="Secure Offline Password Manager",
    author="VaultKeeper Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'cryptography>=42.0.0',
        'keyboard>=0.13.5',
        'qrcode[pil]>=7.4.2',
        'pillow>=10.3.0',
        'pystray>=0.19.0',
        'pyperclip>=1.8.2',
    ],
    entry_points={
        'console_scripts': [
            'vaultkeeper=run:main',
        ],
    },
)