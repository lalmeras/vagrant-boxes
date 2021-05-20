#! /bin/env python3

import os
import sys
import tempfile

import click
import jinja2

@click.command
def vagrant():
    with tempfile.mkdtemp(prefix="vb", dir=os.getcwd()) as temp:
        pass
    sys.exit(0)


def _jinja_environment():
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.getcwd()),
        autoescape=False,
        undefined=jinja2.StrictUndefined
    )
    return env


if __name__ == "__main__":
    vagrant()

def test_unattended_default():
    env = _jinja_environment()
    unattended = "win-10-pro-x64/answer_files/Autounattend.xml.j2"
    rendered_default = env.get_template(unattended).render()
    assert "<UILanguage>en-US</UILanguage>" in rendered_default, \
        "Default locale must be present with default config"
    assert not "<DriverPaths>" in rendered_default, \
        "Extra drivers must be absent with default config"
    assert not "WITHOUT WINDOWS UPDATES" in rendered_default, \
        "Windows Update must be enabled with default config"
    assert "WITH WINDOWS UPDATES" in rendered_default, \
        "Windows Update must be enabled with default config"
    assert "<Value>Windows 10 Pro</Value>" in rendered_default, \
        "Windows 10 Pro installation with default config"
    assert "Pacific Standard Time" in rendered_default, \
        "Pacific Standard timezone with default config"

def test_unattended_custom():
    args = {
        "libvirt": True,
        "windows_version": "Windows 10 Home",
        "locale_language": "fr-FR",
        "timezone": "Romance Standard Time",
        "perform_update": False
    }
    env = _jinja_environment()
    unattended = "win-10-pro-x64/answer_files/Autounattend.xml.j2"
    rendered_custom = env.get_template(unattended).render(**args)
    assert "<UILanguage>fr-FR</UILanguage>" in rendered_custom, \
        "fr-FR must be present with custom config"
    assert "<DriverPaths>" in rendered_custom, \
        "Extra drivers must be present with custom config"
    assert "WITHOUT WINDOWS UPDATES" in rendered_custom, \
        "Windows Update must be disabled with custom config"
    assert not "WITH WINDOWS UPDATES" in rendered_custom, \
        "Windows Update must be disabled with custom config"
    assert "<Value>Windows 10 Home</Value>" in rendered_custom, \
        "Windows 10 Home installation not found with custom config"
    assert "Romance Standard Time" in rendered_custom, \
        "Romance Standard timezone not found with default config"
