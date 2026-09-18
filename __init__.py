import requests
import bisect
import pandas as pd
import psutil
import threading
from requests.exceptions import HTTPError, RequestException
from helpers.pip.utils import process_package, pip_install
from helpers import print_message, print_choices, print_choice, spinning_loader, SUCCESS, INFO, WARNING, ERROR
from concurrent.futures import ThreadPoolExecutor, as_completed


# Module global settings
__module_disabled_methods__ = ['all']
__module_name__ = 'pipHelper'
__module_author__ = 'JoePeach88'
__module_version__ = '1.0.0'
__module_link__ = 'https://github.com/JoePeach88/pip'
__module_category__ = []
__module_compatibility__ = ['all']
__module_dependencies__ = [{}]
__module_status__ = 'stable'
__methods_static_aliases__ = {}


class pipHelper:
    """
    **Module to work with pip packages (extends default pip functionality).**
    """
    def __init__(self, settings: dict):
        self.settings = settings
        self.pypi_url = 'https://pypi.org'
        self.api_url = 'https://pypi.org/simple'
        self.timeout = 30
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) "
                "Gecko/20100101 Firefox/133.0"
            )
        })
        self._packages_sorted = None
        self._package_names_sorted = None

    def all(self):
        """
        **Method returns full list of available packages on pypi.org (this method is disabled).**
        """
        if self._packages_sorted is not None:
            return self._packages_sorted

        response = self._session.get(self.api_url, timeout=self.timeout)
        response.raise_for_status()

        parsed_packages = []

        for line in response.text.splitlines():
            package = process_package(line, self.pypi_url)
            if package is not None:
                parsed_packages.append(package)

        parsed_packages.sort(key=lambda item: item["package"].lower())
        self._packages_sorted = parsed_packages
        self._package_names_sorted = [item["package"].lower() for item in parsed_packages]
        return parsed_packages

    def search(self, package: str, install: bool = False, all: bool = False, version: str = None, limit: int = 200, pretty: bool = True):
        """
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
        """
        limit = int(limit)
        query = package.strip().lower()
        if not query:
            return "Found packages (0):\n" if pretty else []

        packages = self.all()
        names = self._package_names_sorted or []

        left = bisect.bisect_left(names, query)
        right = bisect.bisect_left(names, f"{query}\uffff")
        results = packages[left:right]
        new_results = []
        result_data = []
        if len(results) > limit:
            print_message(f"Found a lot of packages ({len(results)}) with name started with '{package}' only {limit} packages will be returned, if you want to improve return results set --limit flag, but information retrieve will be longer.", WARNING, force=True)
        
        limited_results = results[:limit]
        # Retrieving package info with thread
        physical_cores = psutil.cpu_count(logical=False)
        logical_cores = psutil.cpu_count(logical=True)
        threads_per_core = int(logical_cores / physical_cores)
        minimal_threads = physical_cores * threads_per_core
        workers = min(minimal_threads, max(1, len(results)))
        print_message(f"Starting information retrieve with workers={workers}.")
        stop_signal = threading.Event()
        spinner_thread = threading.Thread(target=spinning_loader, args=(stop_signal,))
        spinner_thread.start()
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self.info, result["package"], False)
                for result in limited_results
                if "package" in result
            ]

            for future in as_completed(futures):
                try:
                    package_info = future.result()
                except Exception:
                    continue
                if isinstance(package_info, dict):
                    new_results.append(package_info)
                else:
                    print_message(f"Returned None package information.", WARNING)
        stop_signal.set()
        spinner_thread.join()

        if not install:
            if not pretty:
                return new_results
            for item in new_results:
                result_data.append({"name": item["name"], "last_version": item["last_version"], "author": item["author_email"]})
            if len(result_data) == 0:
                return "Found packages (0):\n"
            df = pd.DataFrame(result_data)
            return f"Found packages ({len(result_data)}):\n" + df.to_string(index=False, justify='right')
        else:
            if not all:
                first_package = new_results[0]['name']
                package_installation = pip_install(first_package, version)
                if package_installation:
                    return f"Package {first_package} successfully installed."
                else:
                    return f"Package {first_package} not installed, see error above."
            else:
                for install_package in new_results:
                    package_installation = pip_install(install_package['name'], version)
                    if package_installation:
                        return f"Package {install_package['name']} successfully installed."
                    else:
                        return f"Package {install_package['name']} not installed, see error above."

    def info(self, package: str, pretty: bool = True):
        """
        **Display information about a package on pypi.org.**
        ```
        Usage:
            pip info <package>
        ```
        """
        package = package.strip()
        if not package:
            return "Package name is empty." if pretty else None

        json_api = f"https://pypi.org/pypi/{package}/json"

        
        print_message(f"Retrieving information about package '{package}'.")

        try:
            # Thread-safe: avoid sharing one Session across many threads
            response = requests.get(
                json_api,
                timeout=30,
                headers=getattr(self._session, "headers", None),
            )
            response.raise_for_status()
        except HTTPError:
            return f"Package '{package}' not found." if pretty else None
        except RequestException as exc:
            return f"Failed to retrieve package '{package}': {exc}" if pretty else None

        payload = response.json()
        info_data = payload.get("info", {})
        releases = list(payload.get("releases", {}).keys())

        result = {
            "author_email": info_data.get("author_email"),
            "name": info_data.get("name"),
            "release_url": info_data.get("release_url"),
            "requires_dist": info_data.get("requires_dist"),
            "requires_python": info_data.get("requires_python"),
            "last_version": info_data.get("version"),
            "releases": releases,
        }

        if not pretty:
            return result

        releases_text = "\n".join(releases) if releases else "None"
        return (
            f"Name: {result['name']}\n"
            f"Author: {result['author_email']}\n"
            f"Required Python version: {result['requires_python']}\n"
            f"Last version: {result['last_version']}\n"
            f"Other releases:\n{releases_text}"
        )
