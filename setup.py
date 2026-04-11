from setuptools import setup, find_packages
import os
import sys

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read README for long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="vendor-dashboard",
    version="2.0.0",
    description="Comprehensive Vendor Performance Management Dashboard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vendor Analytics Team",
    author_email="vendor.analytics@company.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial",
        "Topic :: Office/Business :: Enterprise",
    ],
    entry_points={
        "console_scripts": [
            "vendor-dashboard=run:main",
            "vendor-api=core.api:start_server",
            "vendor-backup=scripts.auto_backup:main",
        ],
    },
    package_data={
        "vendor_dashboard": [
            "data/*.csv",
            "data/*.db",
            "static/css/*.css",
            "static/js/*.js",
            "static/images/*/*",
            "templates/*.html",
            "workflows/*.yaml",
            "security/*.json",
            "compliance/*.json",
            "locales/*/*.json",
        ],
    },
    project_urls={
        "Documentation": "https://docs.vendor-dashboard.com",
        "Source": "https://github.com/company/vendor-dashboard",
        "Tracker": "https://github.com/company/vendor-dashboard/issues",
    },
)