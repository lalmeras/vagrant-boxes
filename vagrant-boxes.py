#! /bin/env python3

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest.mock

import click
import jinja2


WINDOWS = {
    "pro": "Windows 10 Pro",
    "home": "Windows 10 Home"
}


WINDOWS_TEMPLATES = [
    ("win-10-pro-x64/"),
    ("packer.json", True),
    ("answer_files/Autounattend.xml", False),
]


@click.command("vagrant-boxes")
@click.option("--builders", "-b", multiple=True, default=["virtualbox-iso", "qemu"])
@click.option("--windows", "-w", type=click.Choice(WINDOWS.keys()), default="pro")
@click.option("--locale", "-l", default="en-US")
@click.option("--timezone", "-t", default="Romance Standard Time")
@click.option("--windows-update/--no-windows-update", is_flag=True, default=True)
@click.option("--build/--no-build", is_flag=True, default=True)
@click.option("--clean/--no-clean", is_flag=True, default=True)
def vagrant(builders, windows, locale, timezone, windows_update, build, clean):
    params = {
        "builders": builders,
        "windows_version": WINDOWS[windows],
        "locale_language": locale,
        "timezone": timezone,
        "perform_update": windows_update
    }
    templates = list(WINDOWS_TEMPLATES)
    unattend_template_f = "win-10-pro-x64/answer_files/Autounattend.xml.j2"
    packer_f = "win-10-pro-x64/packer.json.j2"
    temp = tempfile.mkdtemp(prefix="vb", dir=os.getcwd())
    try:
        base = templates.pop(0)
        for template in templates:
            dirname = os.path.dirname(template[0])
            target_dir = os.path.join(temp, dirname)
            source = os.path.join(base, template[0] + ".j2")
            target = os.path.join(temp, template[0])
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            generate_template(source, target, params,
                _jinja_environment(base, template[1]))
        packer_f = os.path.join(temp, templates[0][0])
        if build:
            subprocess.check_call([
                "packer", "build",
                "-var", "source_dir={}".format(os.getcwd()),
                packer_f])
    finally:
        if clean:
            shutil.rmtree(temp, ignore_errors=True)
    sys.exit(0)


def generate_template(source_f, target_f, params, jinja_env):
    with open(source_f, encoding="utf-8") as source:
        source_s = source.read()
    template = jinja_env.from_string(source_s)
    target_s = template.render(**params)
    with open(target_f, "w", encoding="utf-8") as target:
        target.write(target_s)


def _jinja_environment(path, custom_blocks=False):
    if custom_blocks:
        blocks = {
            "block_start_string": "@=",
            "block_end_string": "=@",
            "variable_start_string": "@@",
            "variable_end_string": "@@"
        }
    else:
        blocks = {}
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(path),
        autoescape=False,
        undefined=jinja2.StrictUndefined,
        **blocks
    )
    env.filters["fromjson"] = json.loads
    env.filters['jsonify'] = lambda s: json.dumps(s, indent=2)
    return env


if __name__ == "__main__":
    vagrant()

def test_unattend_default():
    env = _jinja_environment()
    unattend = "win-10-pro-x64/answer_files/Autounattend.xml.j2"
    rendered_default = env.get_template(unattend).render()
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

def test_unattend_custom():
    args = {
        "libvirt": True,
        "windows_version": "Windows 10 Home",
        "locale_language": "fr-FR",
        "timezone": "Romance Standard Time",
        "perform_update": False
    }
    env = _jinja_environment()
    unattend = "win-10-pro-x64/answer_files/Autounattend.xml.j2"
    rendered_custom = env.get_template(unattend).render(**args)
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

def test_generate_template():
    params = {"key": "value"}
    mopen = unittest.mock.mock_open(read_data="content")
    jinja_env = unittest.mock.MagicMock()
    opened = mopen.return_value
    rendered = jinja_env.from_string.return_value
    with unittest.mock.patch("builtins.open", mopen):
        generate_template("source", "target", params, jinja_env)
    mopen.assert_has_calls([
        unittest.mock.call("source", encoding="utf-8"),
        unittest.mock.call("target", "w", encoding="utf-8")
    ], any_order=True)
    # read content
    opened.read.assert_called()
    # build a template instance
    jinja_env.from_string.assert_called_with("content")
    # render with params
    rendered.render.assert_called_with(**params)
    # write result
    opened.write.assert_called_with(rendered.render.return_value)
