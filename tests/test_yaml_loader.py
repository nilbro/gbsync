"""Tests for gbsync.yaml_loader"""

import tempfile
import os
from gbsync.yaml_loader import IncludeLoader
import yaml


def test_yaml_with_include():
    """Test that !include directive loads external files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a SQL file
        sql_file = os.path.join(tmpdir, "query.sql")
        with open(sql_file, "w") as f:
            f.write("SELECT * FROM events")

        # Create YAML that includes it
        yaml_file = os.path.join(tmpdir, "config.yaml")
        with open(yaml_file, "w") as f:
            f.write("sql: !include query.sql")

        # Load and verify
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            with open(yaml_file, "r") as f:
                config = yaml.load(f, Loader=IncludeLoader)
            assert config["sql"] == "SELECT * FROM events"
        finally:
            os.chdir(original_cwd)


def test_yaml_with_multiple_includes():
    """Test YAML with multiple !include directives"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create SQL files
        sql_file1 = os.path.join(tmpdir, "query1.sql")
        with open(sql_file1, "w") as f:
            f.write("SELECT 1")

        sql_file2 = os.path.join(tmpdir, "query2.sql")
        with open(sql_file2, "w") as f:
            f.write("SELECT 2")

        # Create YAML that includes both
        yaml_file = os.path.join(tmpdir, "config.yaml")
        with open(yaml_file, "w") as f:
            f.write("sql1: !include query1.sql\nsql2: !include query2.sql")

        # Load and verify
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            with open(yaml_file, "r") as f:
                config = yaml.load(f, Loader=IncludeLoader)
            assert config["sql1"] == "SELECT 1"
            assert config["sql2"] == "SELECT 2"
        finally:
            os.chdir(original_cwd)
