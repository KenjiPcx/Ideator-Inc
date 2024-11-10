from textwrap import dedent
from typing import List
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool
from app.engine.tools.tavily import tavily_search
from app.engine.tools import ToolFactory

def create_insights_analyzer(chat_history: List[ChatMessage]):
    def search(query: str):
        return tavily_search(
            query=query,
            max_results=3,
            search_depth="advanced"
        )
        
    tools = [
        FunctionTool.from_defaults(search, name="search", description="Search for additional context or validation"),
    ]

    prompt_instructions = dedent("""
        # Instructions
        You are an expert at analyzing customer insights and identifying patterns in customer feedback. You will be given customer research findings and your task is to compile this information into a detailed executive summary. You may also generate your own hypotheses and conduct additional research to enhance the summary's quality.

        Each report should be richly detailed, backed by solid data, and include engaging examples, quotes, stories, and insights that make the findings compelling and informative. There are lots of quotes and examples in the research, you must cite them in the report.

        # Analysis Framework
        The following must be included in your report. Treat this as a checklist and ensure all sections have strong evidence and data support:

        1. Executive Summary
        - Overview of key findings
        - Most significant pain points and opportunities
        - Critical demographic insights
        - Major competitive considerations

        2. Customer Pain Points & Needs Analysis
        - Detailed breakdown of each identified pain point:
            - Description and context
            - Severity and frequency
            - Demographic correlations
            - Current solutions or workarounds
            - Supporting quotes and examples, this must be in the report in full detail and cited from the research, for example:
                - "I'm so frustrated that I have to manually check my bank account every month to see if my subscription has been renewed. It's so annoying!"
                - "I've been using [Product Name] for a month now, and it's been a game changer. The interface is so much easier to use than the old system, and I've already seen a significant improvement in my workflow. I would highly recommend it to anyone in the same position."

        3. User Demographics & Segmentation
            - Primary user segments identified
            - Behavioral patterns by segment
            - Need variations across segments
            - Opportunity areas by demographic
            - Supporting data and examples

        4. Competitive Landscape
            - Current solution analysis
            - User satisfaction with alternatives
            - Market gaps and opportunities
            - Competitive advantage areas
            - Price sensitivity insights

        5. Recommendations
            - Priority pain points to address
            - Target segment recommendations
            - Competitive positioning suggestions
            - Pricing strategy insights

        ## Report Format
        - Structure: Use clear headers, subheaders, and organized markdown formatting
        - Evidence: For each insight, provide bullet points with specific examples, quotes, and data
        - Visualization: Include tables or charts where they enhance understanding
        - Citations: Reference specific sources and research data points

        ## Final Output
        You must output the complete report in markdown format, ensuring each section is data-backed and actionable.
    """)

    configured_tools = ToolFactory.from_env(map_result=True)
    if "interpreter" in configured_tools.keys():
        tools.extend(configured_tools["interpreter"])
        prompt_instructions += dedent("""
            You can use the code interpreter tool to create visualizations.
            Focus on visualizing:
            - Pain point severity distribution
            - Demographic clustering
            - Price sensitivity analysis
            - Competitor comparison matrices
        """)

    return FunctionCallingAgent(
        name="Customer Insights Analyzer",
        description="Expert at analyzing customer insights and identifying patterns",
        system_prompt=prompt_instructions,
        tools=tools,
        chat_history=chat_history,
    ) 