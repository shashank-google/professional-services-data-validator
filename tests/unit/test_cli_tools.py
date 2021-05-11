# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import pytest
from unittest import mock

from data_validation import cli_tools


TEST_CONN = '{"source_type":"Example"}'
CLI_ARGS = {
    "beta": "beta",
    "command": "run",
    "type": "Column",
    "source_conn": TEST_CONN,
    "target_conn": TEST_CONN,
    "tables_list": '[{"schema_name":"my_schema","table_name":"my_table"}]',
    "sum": '["col_a","col_b"]',
    "count": '["col_a","col_b"]',
    "config_file": "example_test.yaml",
    "labels": "name=test_run",
    "threshold": 30.0,
    "verbose": True,
}

CLI_ADD_CONNECTION_ARGS = [
    "connections",
    "add",
    "--connection-name",
    "test",
    "BigQuery",
    "--project-id",
    "example-project",
]

CLI_FIND_TABLES_ARGS = [
    "find-tables",
    "--source-conn",
    TEST_CONN,
    "--target-conn",
    TEST_CONN,
    "--allowed-schemas",
    '["my_schema"]',
]


@mock.patch(
    "argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(**CLI_ARGS),
)
def test_get_parsed_args(mock_args):
    """Test arg parser values."""
    args = cli_tools.get_parsed_args()
    assert args.beta == "beta"
    assert args.command == "run"
    assert args.labels == "name=test_run"
    assert args.threshold == 30.0
    assert args.verbose


def test_configure_arg_parser_list_connections():
    """Test configuring arg parse in different ways."""
    parser = cli_tools.configure_arg_parser()
    args = parser.parse_args(["connections", "list"])

    assert args.command == "connections"
    assert args.connect_cmd == "list"


def test_get_connection_config_from_args():
    """Test configuring arg parse in different ways."""
    parser = cli_tools.configure_arg_parser()
    args = parser.parse_args(CLI_ADD_CONNECTION_ARGS)
    conn = cli_tools.get_connection_config_from_args(args)

    assert conn["project_id"] == "example-project"


def test_create_and_list_connections(capsys, fs):
    # Create Connection
    parser = cli_tools.configure_arg_parser()
    args = parser.parse_args(CLI_ADD_CONNECTION_ARGS)

    conn = cli_tools.get_connection_config_from_args(args)
    cli_tools.store_connection(args.connection_name, conn)

    # List Connection
    cli_tools.list_connections()
    captured = capsys.readouterr()

    assert captured.out == "Connection Name: test\n"


def test_find_tables_config():
    parser = cli_tools.configure_arg_parser()
    args = parser.parse_args(CLI_FIND_TABLES_ARGS)

    allowed_schemas = json.loads(args.allowed_schemas)
    assert allowed_schemas[0] == "my_schema"


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("key=value", [("key", "value")]),
        ("key1=value1,key2=value2", [("key1", "value1"), ("key2", "value2")]),
        (
            "key='longer value',key1='hyphen-value'",
            [("key", "'longer value'"), ("key1", "'hyphen-value'")],
        ),
        ("name=", [("name", "")]),
    ],
)
def test_get_labels(test_input, expected):
    """Test get labels."""
    res = cli_tools.get_labels(test_input)
    assert res == expected


@pytest.mark.parametrize(
    "test_input",
    [
        ("key==value"),
        ("key1=value1,badkey"),
        ("key"),
        (","),
        ("key=value,key"),
        ("key:value"),
    ],
)
def test_get_labels_err(test_input):
    """Ensure that Value Error is raised when incorrect label argument is provided. """
    with pytest.raises(ValueError):
        cli_tools.get_labels(test_input)


@pytest.mark.parametrize(
    "test_input,expected", [(0, 0.0), (50, 50.0), (100, 100.0)],
)
def test_threshold_float(test_input, expected):
    """Test threshold float function."""
    res = cli_tools.threshold_float(test_input)
    assert res == expected


@pytest.mark.parametrize(
    "test_input", [(-4), (float("nan")), (float("inf")), ("string")],
)
def test_threshold_float_err(test_input):
    """Test that threshold float only accepts positive floats."""
    with pytest.raises(argparse.ArgumentTypeError):
        cli_tools.threshold_float(test_input)


def test_get_invalid_json_arg():
    arg_value = "not json"

    with pytest.raises(ValueError):
        cli_tools.get_json_arg(arg_value)


def test_get_json_arg():
    arg_value = '["value"]'
    json_arg = cli_tools.get_json_arg(arg_value)

    assert json_arg == ["value"]
