#!/usr/bin/env python3


import argparse
import pathlib
from dataclasses import dataclass

@dataclass
class Requirement:
    name: str
    version: str
    extra: str | None = None


def parse_requirements_txt(file_path: pathlib.Path) -> dict[str, Requirement]:
    """
    Parse requirements.txt to extract package names and versions.

    :param file_path: Path to requirements.txt
    :return: Dictionary of package names and their versions
    """
    requirements: dict[str, Requirement] = {}
    with file_path.open("r") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if "@" in line:
                continue

            extra = None
            version = None
            if "[" in line:
                # First let's get package name
                bs = line.split("[")

                package = bs[0].strip().lower()

                # Then let's get the extra
                extra = bs[1].split("]")[0]
                extra = extra.strip()

                # Finally, let's get the version
                bs2 = bs[1].split("]")
                bs3 = bs2[1].split("==")
                version = bs3[1].strip()
            elif "==" in line:
                package, version = line.strip().split("==")
            else:
                continue

            requirements[package] = Requirement(package, version, extra)

    return requirements


def update_requirements_in(
    requirements_in_path: pathlib.Path,
    requirements: dict[str, Requirement],
):
    """
    Update requirements.in with versions from requirements dictionary.

    :param requirements_in_path: Path to requirements.in
    :param requirements: Dictionary of package names and versions
    """
    with requirements_in_path.open("r") as file:
        lines = file.readlines()

    with requirements_in_path.open("w") as file:
        for line in lines:
            package_name = line.strip().split("==")[0].split("[")[0].lower()

            line = line.strip()
            new_line = line.strip()

            if package_name in requirements:
                r = requirements[package_name]
                if r.extra:
                    new_line = f"{package_name}[{r.extra}]=={r.version}"
                else:
                    new_line = f"{package_name}=={r.version}"

            print(f"{line} -> {new_line}")
            file.write(new_line + "\n")


def main(args: argparse.Namespace):
    in_path = pathlib.Path(args.requirements_in)  # type: ignore
    if not in_path.exists():
        msg = f"File not found: {in_path}"
        raise FileNotFoundError(msg)
    if in_path.suffix != ".in":
        msg = f"File is not a requirements.in file: {in_path}"
        raise ValueError(msg)

    txt_path = pathlib.Path(args.requirements_txt)  # type: ignore
    if not txt_path.exists():
        msg = f"File not found: {txt_path}"
        raise FileNotFoundError(msg)
    if txt_path.suffix != ".txt":
        msg = f"File is not a requirements.txt file: {txt_path}"
        raise ValueError(msg)

    requirements = parse_requirements_txt(txt_path)

    print(f"Updating {in_path} with versions from {txt_path}")
    update_requirements_in(in_path, requirements)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update requirements.in with versions from requirements.txt",
    )
    parser.add_argument("requirements_in", help="Path to requirements.in")
    parser.add_argument("requirements_txt", help="Path to requirements.txt")

    args = parser.parse_args()

    main(args)
