"""Tests for gbsync.models"""

import pytest
from gbsync.models import FactTableConfig, FactMetricConfig, MetricOperand


def test_fact_table_creation():
    """Test that FactTableConfig model validates required fields"""
    data = {
        "name": "test_table",
        "datasource": "ds_123",
        "userIdTypes": ["user_id"],
        "sql": "SELECT * FROM events"
    }
    table = FactTableConfig(**data)
    assert table.name == "test_table"
    assert table.datasource == "ds_123"
    assert table.userIdTypes == ["user_id"]


def test_fact_metric_ratio_type():
    """Test ratio metric validation"""
    data = {
        "name": "conversion_rate",
        "metricType": "ratio",
        "numerator": {
            "factTableId": "fact_1",
            "column": "conversions"
        },
        "denominator": {
            "factTableId": "fact_1",
            "column": "users"
        }
    }
    metric = FactMetricConfig(**data)
    assert metric.metricType == "ratio"


def test_fact_metric_mean_type():
    """Test mean metric validation"""
    data = {
        "name": "avg_revenue",
        "metricType": "mean",
        "numerator": {
            "factTableId": "fact_1",
            "column": "revenue"
        }
    }
    metric = FactMetricConfig(**data)
    assert metric.metricType == "mean"


def test_metric_operand_with_filters():
    """Test MetricOperand with filters"""
    data = {
        "factTableId": "fact_1",
        "column": "conversions",
        "filters": ["filter_1", "filter_2"]
    }
    operand = MetricOperand(**data)
    assert operand.factTableId == "fact_1"
    assert operand.column == "conversions"
    assert operand.filters == ["filter_1", "filter_2"]


def test_ratio_metric_requires_denominator():
    """Test that ratio metrics require a denominator"""
    data = {
        "name": "conversion_rate",
        "metricType": "ratio",
        "numerator": {
            "factTableId": "fact_1",
            "column": "conversions"
        },
        "denominator": None
    }
    with pytest.raises(ValueError, match="Ratio metrics require a denominator"):
        FactMetricConfig(**data)
