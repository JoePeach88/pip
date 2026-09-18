# pip

**Module to work with pip packages (extends default pip functionality).**

## Methods list

- [info](#info)
- [search](#search)

## Installation

```bash
helper modules install pip --location https://github.com/JoePeach88/pip
```

## Credits

**Author: [JoePeach88](https://github.com/JoePeach88)**

**Version: 1.0.0**

**Supported platforms:**

```
all
```

## Methods

### info

**Display information about a package on pypi.org.**
```
Usage:
pip info <package>
```

### search

**Method searchs pip package on pypi.org.**
>NOTE: Use carefully, not search with minimal query, cause search will be longer.
```
Usage:
1. Only search for package:
pip search <package>
2. Search package and install it (installs first item from list):
pip search <package> --install
3. Search package and install it specified version:
pip search <package> --install --version 1.0.0
4. Search package and install all found packages:
pip search <package> --install --all
```
