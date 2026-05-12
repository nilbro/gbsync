"""Tests for gbsync.client"""

import pytest
from unittest.mock import Mock, patch
from gbsync.client import GrowthBookSyncClient


def test_client_initialization():
    """Test GrowthBookSyncClient can be initialized with credentials"""
    client = GrowthBookSyncClient(
        api_url="https://api.test.com",
        api_key="test_key_123",
        config_file="gbsync.yaml"
    )
    assert client.api_url == "https://api.test.com"
    assert client.api_key == "test_key_123"
    assert client.config_file == "gbsync.yaml"


def test_client_headers():
    """Test that client sets up correct headers with bearer token"""
    api_key = "test_key_123"
    client = GrowthBookSyncClient(
        api_url="https://api.test.com",
        api_key=api_key,
        config_file="gbsync.yaml"
    )
    assert client.headers["Content-Type"] == "application/json"
    assert client.headers["Authorization"] == f"Bearer {api_key}"


def test_client_initial_state():
    """Test that client initializes with empty state"""
    client = GrowthBookSyncClient(
        api_url="https://api.test.com",
        api_key="test_key_123",
        config_file="gbsync.yaml"
    )
    assert client.config is None
    assert client.state is None
    assert client.desired_state is None
    assert client.changes is None
