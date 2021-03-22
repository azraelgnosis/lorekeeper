from distutils.core import setup

setup(
    name="lorekeeper",
    packages=["lorekeeper"],
    version="0.0.1",
    license="MIT",
    description="Uhhh...",
    author="Trevaris",
    author_email="azraelgnosis@gmail.com",
    url="https://github.com/azraelgnosis/",
    download_url="https://github.com/azraelgnosis/lorekeeper/archive/refs/tags/v0.0.2.tar.gz",
    keywords=[],
    install_requires=["flask", "jinja2", "werkzeug"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ]
)