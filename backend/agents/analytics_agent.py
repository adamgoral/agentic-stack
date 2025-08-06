"""
Analytics Agent - Specialized agent for data analysis, visualization, and insights
Handles analytics tasks via A2A, uses built-in Python capabilities for analysis
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator, Union, Tuple
from datetime import datetime, timedelta
import asyncio
import statistics
import re
import csv
import io
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum

from pydantic_ai import Agent
from pydantic_ai.ag_ui import StateDeps

from models.state import ConversationState, AgentTaskState
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Enumeration of data types for analysis"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TIME_SERIES = "time_series"
    TEXT = "text"
    MIXED = "mixed"


@dataclass
class DataSet:
    """Represents a dataset for analysis"""
    raw_data: Any
    parsed_data: List[Any]
    data_type: DataType
    metadata: Dict[str, Any]


class DataAnalyzer:
    """Core data analysis engine with statistical and pattern recognition capabilities"""
    
    def __init__(self):
        self.supported_formats = ["json", "csv", "text", "numeric", "list"]
    
    def parse_data(self, data_input: Any) -> DataSet:
        """
        Parse input data into a standardized format for analysis
        
        Args:
            data_input: Raw data in various formats
            
        Returns:
            DataSet object with parsed and categorized data
        """
        # Handle string input
        if isinstance(data_input, str):
            # Try JSON parsing
            try:
                parsed = json.loads(data_input)
                return self._process_json_data(parsed)
            except json.JSONDecodeError:
                pass
            
            # Try CSV parsing
            if ',' in data_input and '\n' in data_input:
                try:
                    return self._process_csv_data(data_input)
                except:
                    pass
            
            # Try numeric extraction
            numbers = self._extract_numbers(data_input)
            if numbers:
                return DataSet(
                    raw_data=data_input,
                    parsed_data=numbers,
                    data_type=DataType.NUMERIC,
                    metadata={"source": "text_extraction"}
                )
            
            # Treat as text data
            return DataSet(
                raw_data=data_input,
                parsed_data=data_input.split(),
                data_type=DataType.TEXT,
                metadata={"source": "text"}
            )
        
        # Handle list/array input
        elif isinstance(data_input, (list, tuple)):
            return self._process_list_data(list(data_input))
        
        # Handle dictionary input
        elif isinstance(data_input, dict):
            return self._process_json_data(data_input)
        
        # Handle numeric input
        elif isinstance(data_input, (int, float)):
            return DataSet(
                raw_data=data_input,
                parsed_data=[data_input],
                data_type=DataType.NUMERIC,
                metadata={"source": "single_value"}
            )
        
        else:
            # Fallback
            return DataSet(
                raw_data=data_input,
                parsed_data=[str(data_input)],
                data_type=DataType.TEXT,
                metadata={"source": "unknown"}
            )
    
    def _process_json_data(self, data: Union[Dict, List]) -> DataSet:
        """Process JSON data"""
        if isinstance(data, list):
            return self._process_list_data(data)
        
        # Extract numeric values from dict
        numeric_values = []
        categorical_values = []
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                numeric_values.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, (int, float)):
                        numeric_values.append(item)
                    else:
                        categorical_values.append(str(item))
            else:
                categorical_values.append(str(value))
        
        if numeric_values and not categorical_values:
            data_type = DataType.NUMERIC
            parsed_data = numeric_values
        elif categorical_values and not numeric_values:
            data_type = DataType.CATEGORICAL
            parsed_data = categorical_values
        else:
            data_type = DataType.MIXED
            parsed_data = {"numeric": numeric_values, "categorical": categorical_values}
        
        return DataSet(
            raw_data=data,
            parsed_data=parsed_data,
            data_type=data_type,
            metadata={"source": "json", "keys": list(data.keys())}
        )
    
    def _process_csv_data(self, csv_text: str) -> DataSet:
        """Process CSV data"""
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        if not rows:
            return DataSet(
                raw_data=csv_text,
                parsed_data=[],
                data_type=DataType.TEXT,
                metadata={"source": "csv", "error": "empty"}
            )
        
        # Check if first row is header
        headers = rows[0] if len(rows) > 1 else None
        data_rows = rows[1:] if headers else rows
        
        # Try to parse as numeric table
        numeric_columns = defaultdict(list)
        categorical_columns = defaultdict(list)
        
        for row in data_rows:
            for i, value in enumerate(row):
                try:
                    numeric_columns[i].append(float(value))
                except ValueError:
                    categorical_columns[i].append(value)
        
        if numeric_columns and not categorical_columns:
            # Pure numeric data
            all_values = []
            for col in sorted(numeric_columns.keys()):
                all_values.extend(numeric_columns[col])
            return DataSet(
                raw_data=csv_text,
                parsed_data=all_values,
                data_type=DataType.NUMERIC,
                metadata={"source": "csv", "headers": headers, "columns": len(numeric_columns)}
            )
        else:
            # Mixed data
            return DataSet(
                raw_data=csv_text,
                parsed_data={"numeric": numeric_columns, "categorical": categorical_columns},
                data_type=DataType.MIXED,
                metadata={"source": "csv", "headers": headers}
            )
    
    def _process_list_data(self, data: List) -> DataSet:
        """Process list data"""
        if not data:
            return DataSet(
                raw_data=data,
                parsed_data=[],
                data_type=DataType.TEXT,
                metadata={"source": "list", "error": "empty"}
            )
        
        # Check if all numeric
        numeric_values = []
        categorical_values = []
        
        for item in data:
            if isinstance(item, (int, float)):
                numeric_values.append(item)
            elif isinstance(item, str):
                # Try to parse as number
                try:
                    numeric_values.append(float(item))
                except ValueError:
                    categorical_values.append(item)
            elif isinstance(item, dict):
                # Extract numeric values from nested dicts
                for value in item.values():
                    if isinstance(value, (int, float)):
                        numeric_values.append(value)
            else:
                categorical_values.append(str(item))
        
        if numeric_values and not categorical_values:
            return DataSet(
                raw_data=data,
                parsed_data=numeric_values,
                data_type=DataType.NUMERIC,
                metadata={"source": "list", "count": len(numeric_values)}
            )
        elif categorical_values and not numeric_values:
            return DataSet(
                raw_data=data,
                parsed_data=categorical_values,
                data_type=DataType.CATEGORICAL,
                metadata={"source": "list", "count": len(categorical_values)}
            )
        else:
            return DataSet(
                raw_data=data,
                parsed_data={"numeric": numeric_values, "categorical": categorical_values},
                data_type=DataType.MIXED,
                metadata={"source": "list"}
            )
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numbers from text"""
        # Enhanced regex to capture various number formats
        patterns = [
            r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',  # Scientific notation
            r'\$[\d,]+\.?\d*',  # Currency
            r'\d{1,3}(?:,\d{3})*(?:\.\d+)?',  # Comma-separated
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean the match
                clean = match.replace('$', '').replace(',', '')
                try:
                    numbers.append(float(clean))
                except ValueError:
                    continue
        
        return numbers
    
    def calculate_statistics(self, dataset: DataSet) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for the dataset
        
        Args:
            dataset: DataSet object to analyze
            
        Returns:
            Dictionary of statistical measures
        """
        stats = {}
        
        if dataset.data_type == DataType.NUMERIC:
            stats = self._calculate_numeric_stats(dataset.parsed_data)
        elif dataset.data_type == DataType.CATEGORICAL:
            stats = self._calculate_categorical_stats(dataset.parsed_data)
        elif dataset.data_type == DataType.MIXED:
            stats = {
                "numeric": self._calculate_numeric_stats(dataset.parsed_data.get("numeric", [])),
                "categorical": self._calculate_categorical_stats(dataset.parsed_data.get("categorical", []))
            }
        elif dataset.data_type == DataType.TEXT:
            stats = self._calculate_text_stats(dataset.parsed_data)
        
        stats["data_type"] = dataset.data_type.value
        stats["metadata"] = dataset.metadata
        
        return stats
    
    def _calculate_numeric_stats(self, data: Union[List[float], Dict]) -> Dict[str, Any]:
        """Calculate statistics for numeric data"""
        # Handle dict input from mixed data type
        if isinstance(data, dict):
            # Aggregate statistics per column
            column_stats = {}
            all_values = []
            for col_id, col_values in data.items():
                if isinstance(col_values, list) and col_values:
                    all_values.extend(col_values)
                    # Calculate stats for each column
                    if len(col_values) > 0:
                        col_stats = {
                            "count": len(col_values),
                            "mean": statistics.mean(col_values),
                            "min": min(col_values),
                            "max": max(col_values),
                        }
                        if len(col_values) > 1:
                            col_stats["std_dev"] = statistics.stdev(col_values)
                        column_stats[f"column_{col_id}"] = col_stats
            
            # Return aggregated stats for all values combined
            if all_values:
                data = all_values
                result = self._calculate_numeric_stats(data)  # Recursive call with flattened data
                result["column_stats"] = column_stats
                return result
            else:
                return {"error": "No numeric data available", "column_stats": column_stats}
        
        if not data:
            return {"error": "No numeric data available"}
        
        stats = {
            "count": len(data),
            "sum": sum(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "min": min(data),
            "max": max(data),
            "range": max(data) - min(data),
        }
        
        # Additional stats for datasets with more than one value
        if len(data) > 1:
            stats["std_dev"] = statistics.stdev(data)
            stats["variance"] = statistics.variance(data)
            
            # Quartiles
            sorted_data = sorted(data)
            n = len(sorted_data)
            stats["q1"] = sorted_data[n // 4] if n >= 4 else sorted_data[0]
            stats["q3"] = sorted_data[3 * n // 4] if n >= 4 else sorted_data[-1]
            stats["iqr"] = stats["q3"] - stats["q1"]
            
            # Mode (if exists)
            try:
                stats["mode"] = statistics.mode(data)
            except statistics.StatisticsError:
                stats["mode"] = None
            
            # Coefficient of variation
            if stats["mean"] != 0:
                stats["cv"] = (stats["std_dev"] / abs(stats["mean"])) * 100
            
            # Skewness (simplified)
            mean_diff = sum((x - stats["mean"]) ** 3 for x in data)
            stats["skewness"] = mean_diff / (len(data) * stats["std_dev"] ** 3) if stats["std_dev"] > 0 else 0
            
            # Outliers detection using IQR method
            outliers = []
            lower_bound = stats["q1"] - 1.5 * stats["iqr"]
            upper_bound = stats["q3"] + 1.5 * stats["iqr"]
            for value in data:
                if value < lower_bound or value > upper_bound:
                    outliers.append(value)
            stats["outliers"] = outliers
            stats["outlier_count"] = len(outliers)
        
        return stats
    
    def _calculate_categorical_stats(self, data: Union[List[str], Dict]) -> Dict[str, Any]:
        """Calculate statistics for categorical data"""
        # Handle dict input from mixed data type
        if isinstance(data, dict):
            # Flatten all categorical values from dict
            all_categorical = []
            for col_values in data.values():
                if isinstance(col_values, list):
                    all_categorical.extend(str(v) for v in col_values)
            data = all_categorical
        
        if not data:
            return {"error": "No categorical data available"}
        
        counter = Counter(data)
        total = len(data)
        
        stats = {
            "count": total,
            "unique_values": len(counter),
            "most_common": counter.most_common(10),
            "frequency_distribution": dict(counter),
            "mode": counter.most_common(1)[0][0] if counter else None,
        }
        
        # Calculate percentages
        stats["percentages"] = {
            item: (count / total) * 100 for item, count in counter.items()
        }
        
        # Entropy (measure of disorder)
        entropy = 0
        for count in counter.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        stats["entropy"] = entropy
        
        return stats
    
    def _calculate_text_stats(self, data: List[str]) -> Dict[str, Any]:
        """Calculate statistics for text data"""
        if not data:
            return {"error": "No text data available"}
        
        # Join if it's words, otherwise treat as documents
        if all(len(item.split()) == 1 for item in data):
            # Word-level analysis
            word_counter = Counter(data)
            return {
                "total_words": len(data),
                "unique_words": len(word_counter),
                "most_common_words": word_counter.most_common(20),
                "avg_word_length": sum(len(word) for word in data) / len(data) if data else 0,
            }
        else:
            # Document-level analysis
            all_words = []
            for doc in data:
                all_words.extend(doc.split())
            
            word_counter = Counter(all_words)
            return {
                "total_documents": len(data),
                "total_words": len(all_words),
                "unique_words": len(word_counter),
                "most_common_words": word_counter.most_common(20),
                "avg_document_length": len(all_words) / len(data) if data else 0,
            }
    
    def detect_patterns(self, dataset: DataSet) -> Dict[str, Any]:
        """
        Detect patterns and trends in the data
        
        Args:
            dataset: DataSet to analyze
            
        Returns:
            Dictionary of detected patterns
        """
        patterns = {}
        
        if dataset.data_type == DataType.NUMERIC:
            patterns = self._detect_numeric_patterns(dataset.parsed_data)
        elif dataset.data_type == DataType.TIME_SERIES:
            patterns = self._detect_time_series_patterns(dataset.parsed_data)
        elif dataset.data_type == DataType.CATEGORICAL:
            patterns = self._detect_categorical_patterns(dataset.parsed_data)
        
        return patterns
    
    def _detect_numeric_patterns(self, data: List[float]) -> Dict[str, Any]:
        """Detect patterns in numeric data"""
        if len(data) < 2:
            return {"error": "Insufficient data for pattern detection"}
        
        patterns = {}
        
        # Trend detection
        differences = [data[i+1] - data[i] for i in range(len(data)-1)]
        
        if all(d > 0 for d in differences):
            patterns["trend"] = "strictly_increasing"
        elif all(d < 0 for d in differences):
            patterns["trend"] = "strictly_decreasing"
        elif all(d >= 0 for d in differences):
            patterns["trend"] = "increasing"
        elif all(d <= 0 for d in differences):
            patterns["trend"] = "decreasing"
        else:
            # Calculate overall trend using linear regression (simplified)
            n = len(data)
            x_mean = (n - 1) / 2
            y_mean = sum(data) / n
            
            numerator = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator != 0:
                slope = numerator / denominator
                if abs(slope) < 0.01:
                    patterns["trend"] = "stable"
                elif slope > 0:
                    patterns["trend"] = "upward"
                else:
                    patterns["trend"] = "downward"
                patterns["trend_strength"] = abs(slope)
        
        # Periodicity detection (simplified)
        if len(data) >= 4:
            # Check for simple periodicity
            for period in range(2, min(len(data) // 2, 10)):
                is_periodic = True
                for i in range(period, len(data)):
                    if abs(data[i] - data[i - period]) > statistics.stdev(data) if len(data) > 1 else 1:
                        is_periodic = False
                        break
                if is_periodic:
                    patterns["periodicity"] = period
                    break
        
        # Clustering detection
        if len(data) >= 10:
            sorted_data = sorted(data)
            gaps = [sorted_data[i+1] - sorted_data[i] for i in range(len(sorted_data)-1)]
            avg_gap = sum(gaps) / len(gaps)
            large_gaps = [i for i, gap in enumerate(gaps) if gap > 2 * avg_gap]
            
            if large_gaps:
                patterns["clusters"] = len(large_gaps) + 1
                patterns["cluster_boundaries"] = [sorted_data[i] for i in large_gaps]
        
        return patterns
    
    def _detect_time_series_patterns(self, data: List) -> Dict[str, Any]:
        """Detect patterns in time series data"""
        # Simplified time series pattern detection
        return {
            "type": "time_series",
            "note": "Advanced time series analysis would require specialized libraries"
        }
    
    def _detect_categorical_patterns(self, data: List[str]) -> Dict[str, Any]:
        """Detect patterns in categorical data"""
        counter = Counter(data)
        
        patterns = {
            "dominant_category": counter.most_common(1)[0] if counter else None,
            "distribution_type": self._classify_distribution(counter),
        }
        
        # Check for sequential patterns
        if len(data) >= 3:
            sequences = defaultdict(int)
            for i in range(len(data) - 2):
                seq = tuple(data[i:i+3])
                sequences[seq] += 1
            
            if sequences:
                common_sequences = sorted(sequences.items(), key=lambda x: x[1], reverse=True)[:5]
                if common_sequences[0][1] > 1:
                    patterns["recurring_sequences"] = common_sequences
        
        return patterns
    
    def _classify_distribution(self, counter: Counter) -> str:
        """Classify the type of distribution"""
        values = list(counter.values())
        if not values:
            return "empty"
        
        total = sum(values)
        percentages = [v/total for v in values]
        
        # Check for uniform distribution
        if len(set(values)) == 1:
            return "uniform"
        
        # Check for power law (80/20 rule)
        sorted_percentages = sorted(percentages, reverse=True)
        top_20_percent = int(len(sorted_percentages) * 0.2) or 1
        if sum(sorted_percentages[:top_20_percent]) > 0.7:
            return "power_law"
        
        # Check for normal-like distribution
        if len(values) >= 5:
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values)
            within_one_std = sum(1 for v in values if abs(v - mean_val) <= std_val)
            if within_one_std / len(values) > 0.6:
                return "normal_like"
        
        return "irregular"
    
    def generate_insights(self, dataset: DataSet, stats: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """
        Generate human-readable insights from analysis
        
        Args:
            dataset: The analyzed dataset
            stats: Statistical measures
            patterns: Detected patterns
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Insights based on data type
        if dataset.data_type == DataType.NUMERIC:
            insights.extend(self._generate_numeric_insights(stats, patterns))
        elif dataset.data_type == DataType.CATEGORICAL:
            insights.extend(self._generate_categorical_insights(stats, patterns))
        elif dataset.data_type == DataType.MIXED:
            if "numeric" in stats:
                insights.extend(self._generate_numeric_insights(stats["numeric"], patterns))
            if "categorical" in stats:
                insights.extend(self._generate_categorical_insights(stats["categorical"], patterns))
        
        return insights
    
    def _generate_numeric_insights(self, stats: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """Generate insights for numeric data"""
        insights = []
        
        if "mean" in stats and "median" in stats:
            mean_val = stats["mean"]
            median_val = stats["median"]
            
            insights.append(f"The average value is {mean_val:.2f} with a median of {median_val:.2f}")
            
            if abs(mean_val - median_val) > stats.get("std_dev", 0) * 0.5:
                if mean_val > median_val:
                    insights.append("Data shows right skew (mean > median), indicating potential high-value outliers")
                else:
                    insights.append("Data shows left skew (mean < median), indicating potential low-value outliers")
        
        if "outliers" in stats and stats["outliers"]:
            outlier_count = len(stats["outliers"])
            insights.append(f"Detected {outlier_count} outlier{'s' if outlier_count != 1 else ''} that may require investigation")
        
        if "cv" in stats:
            cv = stats["cv"]
            if cv < 10:
                insights.append("Data shows low variability (CV < 10%), indicating consistent values")
            elif cv > 50:
                insights.append("Data shows high variability (CV > 50%), indicating significant dispersion")
        
        if patterns and "trend" in patterns:
            trend = patterns["trend"]
            if trend in ["strictly_increasing", "increasing", "upward"]:
                insights.append(f"Clear upward trend detected in the data")
            elif trend in ["strictly_decreasing", "decreasing", "downward"]:
                insights.append(f"Clear downward trend detected in the data")
            elif trend == "stable":
                insights.append("Data remains relatively stable with no significant trend")
        
        if patterns and "periodicity" in patterns:
            insights.append(f"Data shows periodic behavior with a cycle of {patterns['periodicity']} units")
        
        if patterns and "clusters" in patterns:
            insights.append(f"Data appears to form {patterns['clusters']} distinct clusters")
        
        return insights
    
    def _generate_categorical_insights(self, stats: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """Generate insights for categorical data"""
        insights = []
        
        if "unique_values" in stats:
            unique_count = stats["unique_values"]
            total_count = stats.get("count", 0)
            
            if unique_count == 1:
                insights.append("All values are identical, indicating no variation")
            elif unique_count == total_count:
                insights.append("All values are unique, indicating high diversity")
            else:
                diversity_ratio = unique_count / total_count if total_count > 0 else 0
                if diversity_ratio < 0.1:
                    insights.append(f"Low diversity with only {unique_count} unique values")
                elif diversity_ratio > 0.7:
                    insights.append(f"High diversity with {unique_count} unique values")
        
        if "most_common" in stats and stats["most_common"]:
            top_item, top_count = stats["most_common"][0]
            percentage = (top_count / stats.get("count", 1)) * 100
            insights.append(f"Most frequent value is '{top_item}' occurring {percentage:.1f}% of the time")
        
        if patterns and "distribution_type" in patterns:
            dist_type = patterns["distribution_type"]
            if dist_type == "uniform":
                insights.append("Values are uniformly distributed")
            elif dist_type == "power_law":
                insights.append("Distribution follows power law (80/20 rule) with few values dominating")
            elif dist_type == "normal_like":
                insights.append("Distribution approximates a normal curve")
        
        if "entropy" in stats:
            entropy = stats["entropy"]
            if entropy < 1:
                insights.append("Low entropy indicates predictable/ordered data")
            elif entropy > 3:
                insights.append("High entropy indicates unpredictable/disordered data")
        
        return insights
    
    def recommend_visualizations(self, dataset: DataSet, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recommend appropriate visualizations based on data characteristics
        
        Args:
            dataset: The analyzed dataset
            stats: Statistical measures
            
        Returns:
            List of visualization specifications
        """
        visualizations = []
        
        if dataset.data_type == DataType.NUMERIC:
            # For numeric data
            count = stats.get("count", 0)
            
            if count <= 20:
                visualizations.append({
                    "type": "bar_chart",
                    "title": "Value Distribution",
                    "x_axis": "Index",
                    "y_axis": "Value",
                    "description": "Bar chart showing individual values"
                })
            
            if count >= 10:
                visualizations.append({
                    "type": "histogram",
                    "title": "Frequency Distribution",
                    "x_axis": "Value Range",
                    "y_axis": "Frequency",
                    "bins": min(int(math.sqrt(count)), 20),
                    "description": "Histogram showing value distribution"
                })
                
                visualizations.append({
                    "type": "box_plot",
                    "title": "Statistical Summary",
                    "description": "Box plot showing quartiles, median, and outliers"
                })
            
            if count >= 5:
                visualizations.append({
                    "type": "line_chart",
                    "title": "Trend Analysis",
                    "x_axis": "Sequence",
                    "y_axis": "Value",
                    "description": "Line chart showing value progression"
                })
        
        elif dataset.data_type == DataType.CATEGORICAL:
            # For categorical data
            unique_values = stats.get("unique_values", 0)
            
            if unique_values <= 10:
                visualizations.append({
                    "type": "pie_chart",
                    "title": "Category Distribution",
                    "description": "Pie chart showing proportion of each category"
                })
            
            visualizations.append({
                "type": "bar_chart",
                "title": "Category Frequencies",
                "x_axis": "Category",
                "y_axis": "Count",
                "description": "Bar chart showing frequency of each category"
            })
            
            if unique_values > 5:
                visualizations.append({
                    "type": "horizontal_bar_chart",
                    "title": "Top Categories",
                    "x_axis": "Frequency",
                    "y_axis": "Category",
                    "limit": 10,
                    "description": "Horizontal bar chart of top 10 categories"
                })
        
        elif dataset.data_type == DataType.MIXED:
            # For mixed data
            visualizations.append({
                "type": "dashboard",
                "title": "Multi-faceted Analysis",
                "components": [
                    "numeric_histogram",
                    "category_bar_chart",
                    "correlation_matrix"
                ],
                "description": "Dashboard combining multiple visualizations"
            })
        
        # Add heatmap for correlation if multiple numeric columns
        if dataset.data_type == DataType.MIXED and "numeric" in dataset.parsed_data:
            numeric_data = dataset.parsed_data["numeric"]
            if isinstance(numeric_data, dict) and len(numeric_data) > 1:
                visualizations.append({
                    "type": "heatmap",
                    "title": "Correlation Matrix",
                    "description": "Heatmap showing correlations between numeric variables"
                })
        
        return visualizations


class AnalyticsAgent:
    """
    Analytics agent specialized in data analysis, visualization, and insights generation
    """

    def __init__(
        self, a2a_manager: A2AManager, context_store: ContextStore, model: str = "openai:gpt-4o"
    ):
        self.a2a_manager = a2a_manager
        self.context_store = context_store
        self.is_running = False
        
        # Initialize the data analyzer
        self.data_analyzer = DataAnalyzer()

        # Since we don't have a dedicated MCP server, we'll use empty dict
        self.mcp_servers = {}

        # Create the PydanticAI agent with analytics-specific instructions
        self.agent = Agent(
            model,
            instructions="""You are a specialized analytics agent with expertise in:
            1. Data analysis and pattern recognition
            2. Statistical analysis and calculations
            3. Trend identification and forecasting
            4. Data visualization design and specification
            5. KPI tracking and metrics analysis
            6. Comparative analysis and benchmarking
            
            Your capabilities include:
            - Analyzing data patterns and anomalies
            - Calculating statistical measures (mean, median, standard deviation, correlations)
            - Generating insights from raw data
            - Creating visualization specifications (charts, graphs, dashboards)
            - Identifying trends and making predictions
            - Performing comparative analysis between datasets
            - Generating executive summaries and reports
            
            When handling analytics tasks:
            1. Always validate and clean data before analysis
            2. Use appropriate statistical methods for the data type
            3. Consider sample size and confidence levels
            4. Identify and explain any outliers or anomalies
            5. Provide clear, actionable insights
            6. Suggest appropriate visualizations for the data
            
            For visualization specifications:
            - Recommend chart types based on data characteristics
            - Provide clear axis labels and titles
            - Consider color schemes for accessibility
            - Include relevant annotations and highlights
            
            Always provide:
            - Clear summaries of key findings
            - Statistical confidence levels where applicable
            - Recommendations for action based on insights
            - Visualization specifications that can be implemented
            - Explanations of methodologies used""",
        )

        # Store agent metadata
        self.agent_name = "analytics"
        self.agent_version = "1.0.0"

    async def start(self):
        """Start the analytics agent"""
        self.is_running = True
        logger.info("Analytics agent started")

    async def stop(self):
        """Stop the analytics agent"""
        self.is_running = False
        logger.info("Analytics agent stopped")

    async def process_analytics_task(
        self, task: str, context_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an analytics task
        
        Args:
            task: The analytics task to perform
            context_id: Context ID for the conversation
            metadata: Optional metadata about the task
            
        Returns:
            Analytics results including insights and visualizations
        """
        try:
            logger.info(f"Processing analytics task: {task[:100]}...")

            # Create task state
            task_state = AgentTaskState(
                task_id=metadata.get("task_id") if metadata else None,
                agent_name=self.agent_name,
                status="in_progress",
                input_data={"task": task, "metadata": metadata},
                output_data=None,
                error=None,
            )
            task_state.start()

            # Extract any data from the task if present
            data_context = self._extract_data_context(task, metadata)
            
            # Perform actual data analysis using DataAnalyzer
            analysis_results = {}
            insights = []
            metrics = {}
            visualizations = []
            
            # Try to extract and analyze actual data
            extracted_data = None
            
            # Check if we have data in metadata
            if metadata and "data" in metadata:
                extracted_data = metadata["data"]
            # Try to extract data from the task text
            elif data_context and ("extracted_numbers" in data_context or "provided_data" in data_context):
                extracted_data = data_context.get("provided_data") or data_context.get("extracted_numbers")
            # Try to parse JSON or CSV from the task itself
            else:
                # Look for JSON structure in task
                json_match = re.search(r'\{[^}]*\}|\[[^\]]*\]', task)
                if json_match:
                    try:
                        extracted_data = json.loads(json_match.group())
                    except:
                        pass
                
                # Look for CSV-like structure
                if not extracted_data and '\n' in task and ',' in task:
                    lines = task.split('\n')
                    csv_lines = [line for line in lines if ',' in line]
                    if csv_lines:
                        extracted_data = '\n'.join(csv_lines)
            
            # Perform analysis if we have data
            if extracted_data:
                try:
                    # Parse the data
                    dataset = self.data_analyzer.parse_data(extracted_data)
                    
                    # Calculate statistics
                    stats = self.data_analyzer.calculate_statistics(dataset)
                    metrics = stats
                    
                    # Detect patterns
                    patterns = self.data_analyzer.detect_patterns(dataset)
                    
                    # Generate insights
                    insights = self.data_analyzer.generate_insights(dataset, stats, patterns)
                    
                    # Recommend visualizations
                    visualizations = self.data_analyzer.recommend_visualizations(dataset, stats)
                    
                    # Store analysis results
                    analysis_results = {
                        "dataset_type": dataset.data_type.value,
                        "statistics": stats,
                        "patterns": patterns,
                        "data_summary": {
                            "type": dataset.data_type.value,
                            "metadata": dataset.metadata
                        }
                    }
                    
                except Exception as e:
                    logger.warning(f"Error in data analysis: {e}")
                    # Fall back to extraction methods
                    insights = []
                    metrics = {}

            # Run the LLM agent for contextual analysis and interpretation
            async with self.agent as agent:
                # Enhance the prompt with actual analysis results
                analytics_prompt = f"""
                Analytics Task: {task}
                
                {f"Computed Statistics: {json.dumps(metrics, indent=2, default=str)}" if metrics else ""}
                {f"Detected Patterns: {json.dumps(patterns if 'patterns' in locals() else {}, indent=2, default=str)}" if extracted_data else ""}
                {f"Generated Insights: {json.dumps(insights, indent=2)}" if insights else ""}
                
                Based on the above analysis, please provide:
                1. Interpretation of the statistical findings
                2. Business implications of the patterns detected
                3. Additional context and recommendations
                4. Any risks or concerns identified
                5. Next steps for deeper analysis
                
                Focus on making the analysis actionable and easy to understand.
                """

                # Execute the analytics task
                response = await agent.run(analytics_prompt)

                # Combine automated analysis with LLM interpretation
                combined_insights = insights + self._extract_insights(str(response))
                combined_insights = list(set(combined_insights))[:15]  # Dedupe and limit
                
                # Process and structure the results
                results = {
                    "analysis": str(response),
                    "insights": combined_insights,
                    "metrics": metrics if metrics else self._extract_metrics(str(response), data_context),
                    "visualizations": visualizations if visualizations else self._extract_visualization_specs(str(response)),
                    "recommendations": self._extract_recommendations(str(response)),
                    "computed_analysis": analysis_results if analysis_results else None,
                    "timestamp": datetime.utcnow().isoformat(),
                    "task_id": task_state.task_id,
                    "agent": self.agent_name,
                }

                # Update task state
                task_state.complete(results)
                await self.context_store.store_task(task_state)

                logger.info(f"Analytics task completed: {task_state.task_id}")
                return results

        except Exception as e:
            logger.error(f"Error processing analytics task: {e}")
            if 'task_state' in locals():
                task_state.fail(str(e))
                await self.context_store.store_task(task_state)
            raise

    def _extract_data_context(self, task: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract data context from task and metadata"""
        context = {}
        
        # Extract numbers from the task
        numbers = re.findall(r'\d+\.?\d*', task)
        if numbers:
            context["extracted_numbers"] = [float(n) if '.' in n else int(n) for n in numbers]
        
        # Add any data from metadata
        if metadata and "data" in metadata:
            context["provided_data"] = metadata["data"]
        
        # Look for time-related keywords
        time_keywords = ["daily", "weekly", "monthly", "yearly", "hourly", "quarterly"]
        for keyword in time_keywords:
            if keyword.lower() in task.lower():
                context["time_period"] = keyword
                break
        
        return context

    def _extract_insights(self, response: str) -> List[str]:
        """Extract key insights from the response"""
        insights = []
        
        # Look for insight patterns
        insight_patterns = [
            r'(?:insight|finding|observation|discovery)[:.]?\s*(.+?)(?:\.|$)',
            r'(?:shows?|indicates?|suggests?|reveals?)\s+that\s+(.+?)(?:\.|$)',
            r'(?:significant|notable|important)\s+(.+?)(?:\.|$)',
        ]
        
        for pattern in insight_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
            insights.extend(matches)
        
        # Also look for bullet points that might be insights
        bullet_pattern = r'[-•*]\s+(.+?)(?:\n|$)'
        bullet_matches = re.findall(bullet_pattern, response)
        for match in bullet_matches:
            if any(word in match.lower() for word in ["increase", "decrease", "trend", "pattern", "correlation", "average", "peak", "anomaly"]):
                insights.append(match.strip())
        
        return list(set(insights))[:10]  # Return top 10 unique insights

    def _extract_metrics(self, response: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics and calculations from the response"""
        metrics = {}
        
        # If we have actual data, calculate real statistics
        if data_context and "extracted_numbers" in data_context:
            numbers = data_context["extracted_numbers"]
            if numbers:
                metrics["calculated"] = {
                    "count": len(numbers),
                    "mean": statistics.mean(numbers),
                    "median": statistics.median(numbers),
                    "min": min(numbers),
                    "max": max(numbers),
                }
                if len(numbers) > 1:
                    metrics["calculated"]["std_dev"] = statistics.stdev(numbers)
        
        # Extract metrics mentioned in the response
        metric_patterns = [
            (r'average[:\s]+?([\d.]+)', "average"),
            (r'mean[:\s]+?([\d.]+)', "mean"),
            (r'median[:\s]+?([\d.]+)', "median"),
            (r'total[:\s]+?([\d.]+)', "total"),
            (r'sum[:\s]+?([\d.]+)', "sum"),
            (r'count[:\s]+?([\d.]+)', "count"),
            (r'percentage[:\s]+?([\d.]+)%?', "percentage"),
            (r'growth[:\s]+?([\d.]+)%?', "growth_rate"),
            (r'correlation[:\s]+?([\d.]+)', "correlation"),
        ]
        
        metrics["extracted"] = {}
        for pattern, name in metric_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                metrics["extracted"][name] = float(match.group(1))
        
        return metrics

    def _extract_visualization_specs(self, response: str) -> List[Dict[str, Any]]:
        """Extract visualization specifications from the response"""
        visualizations = []
        
        # Common chart types to look for
        chart_types = [
            "bar chart", "line chart", "pie chart", "scatter plot", 
            "histogram", "heatmap", "box plot", "area chart",
            "dashboard", "gauge", "funnel", "treemap"
        ]
        
        for chart_type in chart_types:
            if chart_type.lower() in response.lower():
                # Try to extract context around the chart mention
                pattern = rf'({chart_type}[^.]*\.)'
                matches = re.findall(pattern, response, re.IGNORECASE)
                
                for match in matches:
                    viz_spec = {
                        "type": chart_type.replace(" ", "_").lower(),
                        "description": match.strip(),
                    }
                    
                    # Extract axis labels if mentioned
                    x_axis_pattern = r'x[- ]axis[:=]\s*([^,\n]+)'
                    y_axis_pattern = r'y[- ]axis[:=]\s*([^,\n]+)'
                    
                    x_match = re.search(x_axis_pattern, match, re.IGNORECASE)
                    y_match = re.search(y_axis_pattern, match, re.IGNORECASE)
                    
                    if x_match:
                        viz_spec["x_axis"] = x_match.group(1).strip()
                    if y_match:
                        viz_spec["y_axis"] = y_match.group(1).strip()
                    
                    visualizations.append(viz_spec)
        
        # If no specific charts mentioned, provide a default recommendation
        if not visualizations and "data" in response.lower():
            visualizations.append({
                "type": "bar_chart",
                "description": "Recommended visualization for data analysis",
                "auto_generated": True
            })
        
        return visualizations[:5]  # Return top 5 visualization specs

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from the response"""
        recommendations = []
        
        # Look for recommendation patterns
        rec_patterns = [
            r'(?:recommend|suggest|advise|propose)[:\s]+(.+?)(?:\.|$)',
            r'(?:should|could|would)\s+(?:consider|implement|analyze|investigate)\s+(.+?)(?:\.|$)',
            r'(?:next steps?|action items?)[:\s]+(.+?)(?:\.|$)',
        ]
        
        for pattern in rec_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
            recommendations.extend(matches)
        
        return list(set(recommendations))[:5]  # Return top 5 unique recommendations

    async def handle_a2a_request(
        self, message: str, context_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an A2A request from another agent
        
        Args:
            message: The task message
            context_id: Context ID for the conversation
            metadata: Optional metadata
            
        Returns:
            Task result for A2A response
        """
        try:
            # Process the analytics task
            results = await self.process_analytics_task(message, context_id, metadata)

            # Format for A2A response
            return {
                "status": "completed",
                "result": results,
                "artifacts": {
                    "insights": results.get("insights", []),
                    "metrics": results.get("metrics", {}),
                    "visualizations": results.get("visualizations", []),
                    "recommendations": results.get("recommendations", []),
                },
                "metadata": {
                    "agent": self.agent_name,
                    "version": self.agent_version,
                    "model": self.agent.model,
                },
            }

        except Exception as e:
            logger.error(f"Error handling A2A request: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "metadata": {
                    "agent": self.agent_name,
                    "version": self.agent_version,
                },
            }

    async def run_ag_ui(self, message: str, state: ConversationState) -> AsyncGenerator[str, None]:
        """
        Process a request and stream AG-UI events
        For direct frontend communication (if needed)
        """
        try:
            # Start event
            yield json.dumps(
                {
                    "type": "start",
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_id": state.context_id,
                    "agent": self.agent_name,
                }
            )

            # Status update
            yield json.dumps(
                {"type": "status", "message": "Analyzing data..."}
            )

            # Process the analytics task
            results = await self.process_analytics_task(message, state.context_id)

            # Stream the results
            yield json.dumps({
                "type": "text_message",
                "content": results["analysis"],
                "metadata": {
                    "insights": results.get("insights", []),
                    "metrics": results.get("metrics", {}),
                    "visualizations": results.get("visualizations", []),
                    "recommendations": results.get("recommendations", []),
                }
            })

            # Complete event
            yield json.dumps({
                "type": "complete",
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in AG-UI execution: {e}")
            yield json.dumps({"type": "error", "message": str(e)})

    def to_a2a(self):
        """Convert to A2A server for agent-to-agent communication"""
        return self.agent.to_a2a()

    def to_ag_ui(self):
        """Convert to AG-UI server for frontend communication"""
        return self.agent.to_ag_ui()

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "agent": self.agent_name,
            "version": self.agent_version,
            "status": "running" if self.is_running else "stopped",
            "model": self.agent.model,
            "capabilities": "built-in Python analytics",
        }

    async def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities"""
        return [
            "data_analysis",
            "statistical_analysis",
            "pattern_recognition",
            "trend_analysis",
            "metric_calculation",
            "kpi_tracking",
            "visualization_design",
            "comparative_analysis",
            "anomaly_detection",
            "forecasting",
            "correlation_analysis",
            "summary_generation",
        ]