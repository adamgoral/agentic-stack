"""
Analytics Agent - Specialized agent for data analysis, visualization, and insights
Handles analytics tasks via A2A, uses built-in Python capabilities for analysis
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import asyncio
import statistics
import re
from collections import Counter, defaultdict

from pydantic_ai import Agent
from pydantic_ai.ag_ui import StateDeps

from models.state import ConversationState, AgentTaskState
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore

logger = logging.getLogger(__name__)


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

            # Run the analytics task
            async with self.agent as agent:
                # Enhance the prompt with analytics-specific guidance
                analytics_prompt = f"""
                Analytics Task: {task}
                
                {f"Data Context: {json.dumps(data_context, indent=2)}" if data_context else ""}
                
                Please perform thorough analysis on this task. Consider:
                1. Identify key metrics and KPIs
                2. Calculate relevant statistics
                3. Identify patterns, trends, and anomalies
                4. Generate actionable insights
                5. Recommend appropriate visualizations
                
                Provide a comprehensive response that includes:
                - Summary statistics and calculations
                - Key findings and insights
                - Trend analysis if applicable
                - Visualization recommendations with specifications
                - Actionable recommendations based on the analysis
                """

                # Execute the analytics task
                response = await agent.run(analytics_prompt)

                # Process and structure the results
                results = {
                    "analysis": str(response),
                    "insights": self._extract_insights(str(response)),
                    "metrics": self._extract_metrics(str(response), data_context),
                    "visualizations": self._extract_visualization_specs(str(response)),
                    "recommendations": self._extract_recommendations(str(response)),
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