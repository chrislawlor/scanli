"""
Reqs:
    requirements-parser
"""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import List

import requests
import requirements
from rich.console import Console
from rich.progress import track
from rich.table import Table
from cache_to_disk import cache_to_disk

PYPI_URL = "https://pypi.org/pypi/%s/json"

# Normalize License texts

LICENSE_ALIASES = {
    "MIT": ["MIT", "MIT License"],
    "Apache": ["Apache", "Apache Software License"],
    "Apache 2": [
        "Apache License 2.0",
        "Apache-2.0",
        "Apache2",
        "Apache 2",
        "Apache-2",
        "Apache 2.0",
        "Apache License, Version 2.0",
        "http://www.apache.org/licenses/LICENSE-2.0",
    ],
    "BSD": ["BSD", "BSD License"],
    "PSF": ["Python", "Python Software Foundation License"],
    "LGPL": ["LGPL", "GNU LGPL"],
}

LICENSE_ALIASES_REVERSE = {
    alias.lower(): lic for lic, aliases in LICENSE_ALIASES.items() for alias in aliases
}


def normalize_license(lic) -> str:
    if not lic:
        return ""
    lower = lic.lower().strip()
    if lower in LICENSE_ALIASES_REVERSE:
        return LICENSE_ALIASES_REVERSE[lower]
    return lic


@dataclass
class ProjectUrls:
    documentation: str
    funding: str
    homepage: str
    release_notes: str
    source: str
    tracker: str


@dataclass
class PipMetadata:
    name: str
    description: str
    description_content_type: str
    classifiers: List[str]
    license: str
    urls: ProjectUrls
    requires_dist: List[str]

    def get_license(self):
        # If the license is really long, it's probably the
        # entire license text. In that case, try getting it from the
        # classifier
        if self.license and len(self.license) < 100:
            return self.license
        for classifier in self.classifiers:
            if classifier.startswith("License"):
                return classifier.split("::")[-1]
        return self.license or ""

    def get_normalized_license(self):
        return normalize_license(self.get_license())


# Pip


@cache_to_disk(1)
def pip_fetch_metadata(package_name: str) -> PipMetadata:
    url = PYPI_URL % package_name
    resp = requests.get(url)
    data = resp.json()

    info = data.get("info", {})
    url_data = info.get("project_urls", {})
    urls = ProjectUrls(
        documentation=url_data.get("Documentation", ""),
        funding=url_data.get("Funding", ""),
        homepage=url_data.get("Homepage", ""),
        release_notes=url_data.get("Release notes", ""),
        source=url_data.get("Source", ""),
        tracker=url_data.get("Tracker", ""),
    )
    return PipMetadata(
        name=package_name,
        description=info.get("description", ""),
        description_content_type=info.get("description_content_type", ""),
        classifiers=info.get("classifiers", []),
        license=info.get("license", "") or "",
        urls=urls,
        requires_dist=info.get("requires_dist"),
    )


def pip_read_requirements_file(file) -> List[str]:
    reqs: List[str] = []
    with open(file) as f:
        for req in requirements.parse(f):
            if req.name is not None:
                reqs.append(req.name)
    return reqs


def display_stats(metadatas: List[PipMetadata]):

    has_license = 0
    has_requires_dist = 0
    for md in metadatas:
        if md.get_license():
            has_license += 1
        if md.requires_dist:
            has_requires_dist += 1

    print(f"Has license: {has_license/len(metadatas) * 100}")
    print(f"has requires_dist: {has_requires_dist/len(metadatas) * 100}")

    packages_by_license = defaultdict(list)
    for md in metadatas:
        lic = md.get_normalized_license()[:80].strip()
        packages_by_license[lic].append(md.name)

    licenses = [md.get_normalized_license()[:80].strip() for md in metadatas]
    counts = Counter(licenses)

    table = Table(title="License counts", show_lines=True)
    table.add_column("License")
    table.add_column("Count", justify="right")
    table.add_column("Packages")
    for lic, count in counts.most_common():
        if count < 10 or not lic:
            table.add_row(lic, str(count), ", ".join(packages_by_license[lic]))
        else:
            table.add_row(lic, str(count), "")

    console = Console()
    console.print(table)


# CLI Commands


def scan_cli(pip: str):
    reqs = pip_read_requirements_file(pip)

    metadatas = []
    for req in track(reqs, description="Fetching package metadata from pypi"):
        metadatas.append(pip_fetch_metadata(req))

    display_stats(metadatas)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="scanli: CLI tool for license tracking."
    )
    subparsers = parser.add_subparsers()

    # scan parser
    parser_scan = subparsers.add_parser("scan")
    parser_scan.add_argument("-p", "--pip")
    parser_scan.set_defaults(func=scan_cli)

    args = parser.parse_args()
    argsd = args.__dict__
    func = argsd.pop("func")
    func(**argsd)
