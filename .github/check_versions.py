import yaml
from contextlib import contextmanager
import requirements
import pathlib
import os


@contextmanager
def read_conda_yaml(path):
    with open(path, "rb") as config_file:
        # Toss out the first line that declares the version since its not supported YAML syntax
        next(config_file)
        yield yaml.safe_load(config_file)


def standardize_format(packages):
    standardized_package_specifiers = []
    for package in packages:
        if package.specs:
            all_specs = ",".join([''.join(spec) for spec in package.specs])
            standardized = f"{package.name}{all_specs}"
        else:
            standardized = package.name
        standardized_package_specifiers.append(standardized)
    return standardized_package_specifiers


def get_evalml_conda_requirements(conda_recipe):
    with read_conda_yaml(conda_recipe) as recipe:
        core_reqs = recipe['outputs'][0]['requirements']['run']
        extra_reqs = recipe['outputs'][1]['requirements']['run']
        extra_reqs = [
            package for package in extra_reqs if "evalml-core" not in package]
        all_reqs = core_reqs + extra_reqs
    return standardize_format(requirements.parse("\n".join(all_reqs)))


def check_versions():
    conda_recipe_file_path = pathlib.Path(pathlib.Path("recipe", "meta.yaml"))
    latest_recipe_file_path = pathlib.Path(
        os.getcwd(), "evalml", ".github", "meta.yaml")
    conda_versions = sorted(
        get_evalml_conda_requirements(conda_recipe_file_path))
    latest_conda_versions = sorted(
        get_evalml_conda_requirements(latest_recipe_file_path))
    if conda_versions != latest_conda_versions:
        not_in_latest = set(conda_versions).difference(
            latest_conda_versions)
        not_in_latest = ["\t" + version for version in not_in_latest]
        not_in_latest = "\n".join(not_in_latest)

        not_in_master = set(
            latest_conda_versions).difference(conda_versions)
        not_in_master = ["\t" + version for version in not_in_master]
        not_in_master = "\n".join(not_in_master)

        raise SystemExit(
            f"The following package versions are in master but different from latest evalml recipe:\n {not_in_latest}\n"
            f"The following package versions are in latest evalml recipe but different from master branch:\n {not_in_master}\n"
            "Please make changes to the recipe so that they match if this is a version upgrade pr."
        )


if __name__ == "__main__":
    check_versions()
