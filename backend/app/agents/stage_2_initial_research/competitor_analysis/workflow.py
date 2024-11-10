import json
from textwrap import dedent
from typing import List, Optional
from app.agents.stage_2_initial_research.competitor_analysis.competitor_searcher import CompetitorInfo, CompetitorSearchResponse, create_competitor_searcher
from app.agents.stage_2_initial_research.competitor_analysis.competitor_analyzer import create_competitor_analyzer
from app.agents.stage_2_initial_research.competitor_analysis.report_critic import CompetitorReportCritique, create_report_critic
from app.agents.stage_2_initial_research.competitor_analysis.competitor_researcher import SearchCompetitorDetailsResponse, create_competitor_researcher
from app.agents.example.reporter import create_reporter
from app.engine.tools.file_writer import write_file
from app.utils.json_extractor import extract_code_block_from_response, extract_json_from_response
from app.utils.json_validator import JsonValidationHelper
from app.workflows.react import ReActAgentWithMemory
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from app.workflows.single import AgentRunEvent, FunctionCallingAgent, AgentRunResult
from llama_index.core.chat_engine.types import ChatMessage
import asyncio
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.prompts.base import PromptTemplate
from app.settings import Settings

class ExecuteSearchEvent(Event):
    query: str

class CombineSearchesEvent(Event):
    pass
    
class FindCompetitorsEvent(Event):
    input: str

class GatherCompetitorDetailsEvent(Event):
    input: CompetitorInfo

class CombineCompetitorDetailsEvent(Event):
    pass
    
class AnalyzeCompetitorsEvent(Event):
    input: str
    
class CritiqueCompetitorsEvent(Event):
    input: str
    
class ReportEvent(Event):
    input: str

class CompetitorAnalysisWorkflow(Workflow):
    """
    A workflow that performs competitor analysis through multiple stages:
    1. Search for competitors
    2. Gather detailed information about each competitor
    3. Analyze the competitors
    4. Critique and refine the analysis
    5. Generate a final report
    
    Args:
        chat_history: Previous chat messages for context
        num_searches: Number of parallel searches to perform
        num_competitors: Maximum number of competitors to analyze
        timeout: Maximum time in seconds for the workflow
    """
    def __init__(self, 
                 session_id: str,
                 chat_history: Optional[List[ChatMessage]] = None,
                 num_searches: int = 2,
                 num_competitors: int = 4,
                 timeout: int = 360,
                 max_critic_iterations: int = 3):
        super().__init__(timeout=timeout)
        self.session_id = session_id
        self.chat_history = chat_history or []
        self.num_searches = num_searches
        self.num_competitors = num_competitors
        self.max_critic_iterations = max_critic_iterations
        
    @step()
    async def start(self, ctx: Context, ev: StartEvent) -> ExecuteSearchEvent:
        '''
        Start the workflow by setting the task and generating search queries
        '''
        # EXAMPLE: task = "Perform a competitive analysis on the following product idea: " + ev.input
        ctx.data["task"] = ev.input
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Research starter",
                msg=f"Starting research on task: {ev.input}",
            )
        )
        
        # Generate search queries
        queries = await self._generate_search_queries(ev.input, 
                                                      chat_history=[], 
                                                      number_of_queries=self.num_searches)
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Research starter",
                msg=f"Generated {len(queries)} search queries\n{queries}",
            )
        )
        for query in queries[:self.num_searches]:
            ctx.send_event(ExecuteSearchEvent(query=query))
            
        return None

    @step(num_workers=2)
    async def execute_search(self, ctx: Context, ev: ExecuteSearchEvent) -> CombineSearchesEvent:
        '''
        Execute a single search query and fires an event to search each competitor
        '''
        prompt = f"""
                We are currently researching this task: {ctx.data["task"]}
                Here is the search query you should use for your research: {ev.query}
            """
        competitor_searcher = create_competitor_searcher(chat_history=[])
        result = await self.run_agent(ctx, competitor_searcher, prompt)
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=competitor_searcher.name,
                msg=f"Completed competitor search: {result.response.message.content}",
            )
        )
        
        parser = JsonValidationHelper(CompetitorSearchResponse, Settings.llm)
        parsed_res = await parser.validate_and_fix(result.response.message.content)
        
        if not parsed_res:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=competitor_searcher.name,
                    msg=f"No valid JSON content found in the response",
                )
            )
            ctx.data["num_searches_completed"] = ctx.data.get("num_searches_completed", 0) + 1
            return CombineSearchesEvent()
        
        # This will be used by the analyzer agent
        ctx.data.setdefault("initial_search_results", []).append(result.response.message.content)
        ctx.data.setdefault("sources", []).extend(parsed_res.sources)
        ctx.write_event_to_stream(
                AgentRunEvent(
                    name=competitor_searcher.name,
                    msg=f"Found {len(parsed_res.competitors)} competitors",
                )
            )
        
        for competitor in parsed_res.competitors:
            # Skip if we've already gathered details for this competitor
            if competitor.name in ctx.data.get("competitor_names", set()):
                continue 
            
            ctx.data.setdefault("competitor_names", set()).add(competitor.name)
            ctx.data.setdefault("competitors", []).append(competitor)
            
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=competitor_searcher.name,
                    msg=f"Shortlisted {competitor.name} as a competitor",
                )
            )
        
        ctx.data["num_searches_completed"] = ctx.data.get("num_searches_completed", 0) + 1
        return CombineSearchesEvent()
    
    @step()
    async def combine_searches(self, ctx: Context, ev: CombineSearchesEvent) -> GatherCompetitorDetailsEvent:
        '''
        Rerank and deduplicate competitors
        '''
        # If we haven't completed all searches, wait for more
        num_searches_completed = ctx.data.get("num_searches_completed", 0)
        if num_searches_completed < self.num_searches:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Research combiner",
                    msg=f"Completed {num_searches_completed} out of {self.num_searches} searches",
                )
            )
            return None
        
        # Otherwise, we should have collected all competitor details, rerank and deduplicate them
        ctx.collect_events(ev, [CombineSearchesEvent] * self.num_searches)
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Research combiner",
                msg=f"All competitor searches have been completed, here are the potential competitors we found:\n{ctx.data['competitor_names']}",
            )
        )
        
        reranked_competitors = await self._deduplicate_and_rank_competitors(ctx.data["competitors"], ctx.data["task"], self.num_competitors)
        ctx.data["reranked_competitors"] = reranked_competitors
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Research combiner",
                msg=f"Shortlisted {len(reranked_competitors)} promising competitors:\n{reranked_competitors}",
            )
        )
        
        for competitor in reranked_competitors:
            ctx.send_event(GatherCompetitorDetailsEvent(input=competitor))
        
        return None
        
    
    @step(num_workers=2)
    async def gather_competitor_details(self, ctx: Context, ev: GatherCompetitorDetailsEvent) -> CombineCompetitorDetailsEvent:
        '''
        Gather details about a single competitor, including pricing information, key features, target audience, and reviews
        '''
        prompt = f"""
                We are currently researching this task: {ctx.data["task"]}
                You are tasked with gathering details about this competitor: {ev.input}
            """
        competitor_researcher = create_competitor_researcher([])
        result = await self.run_agent(ctx, competitor_researcher, prompt)
        ctx.data.setdefault("refined_search_results", []).append(result.response.message.content)
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=competitor_researcher.name,
                msg=f"Completed competitor detail gathering: {result.response.message.content}",
            )
        )
        
        parser = JsonValidationHelper(SearchCompetitorDetailsResponse, Settings.llm)
        parsed_res = await parser.validate_and_fix(result.response.message.content)
        
        if not parsed_res:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=competitor_researcher.name,
                    msg=f"No JSON content found in the response",
                )
            )
            return CombineCompetitorDetailsEvent()

        ctx.data.setdefault("sources", []).extend(parsed_res.sources)
        return CombineCompetitorDetailsEvent()
    
    @step()
    async def combine_competitor_details(self, ctx: Context, ev: CombineCompetitorDetailsEvent) -> AnalyzeCompetitorsEvent:
        '''
        Combine the details about all competitors
        '''
        num_to_collect = len(ctx.data.get("reranked_competitors"))
        num_completed = len(ctx.data.get("refined_search_results"))
        
        if num_completed < num_to_collect:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Research combiner",
                    msg=f"Collected {num_completed} out of {num_to_collect} competitor details",
                )
            )
            return None
        
        # At this point, we should have collected all competitor details
        ctx.collect_events(ev, [CombineCompetitorDetailsEvent] * num_to_collect)
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Research combiner",
                msg=f"All competitor details have been collected, reranking and deduplicating competitors",
            )
        )
        
        return AnalyzeCompetitorsEvent(input="All competitor details have been collected")
    
    @step()
    async def analyze(
        self, ctx: Context, ev: AnalyzeCompetitorsEvent, competitor_analyzer: FunctionCallingAgent
    ) -> CritiqueCompetitorsEvent | ReportEvent:
        if ctx.data.get("critic_iteration", 0) == 0:
            prompt = dedent(f"""
                We are currently researching this task: {ctx.data['task']}
                
                ### Initial research
                Junior analysts have gathered initial research on these competitors.
                They have found the following competitors: 
                {ctx.data["competitor_names"]}
                
                Here are their findings and analysis: 
                {ctx.data["initial_search_results"]}
                
                ### Refined research
                Promising competitors have been reranked and deduplicated and further researched, here are their details: 
                {ctx.data["refined_search_results"]}
                
                ### Report
                Analyze the data and provide a detailed report with citations
            """)
        else:
            prompt = dedent(f"""
                We are currently researching this task: {ctx.data['task']}
                
                You had asked the critic to critique your output and here is the feedback: {ev.input}
                
                Refine this report based on the following feedback: {ev.input}
            """)
        result: AgentRunResult = await self.run_agent(ctx, competitor_analyzer, prompt)
        ctx.data["competitor_analysis_result"] = result.response.message.content
        
        # If we've done this 3 times, we should just return the report
        if ctx.data.get("critic_iteration", 0) >= self.max_critic_iterations:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=competitor_analyzer.name,
                    msg=f"Completed competitor analysis and asked the critic 3 times, moving on to generate the final report",
                )
            )
            return ReportEvent(input=ctx.data["competitor_analysis_result"])
        
        # Otherwise, we should critique the report
        ctx.data["critic_iteration"] = ctx.data.get("critic_iteration", 0) + 1
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=competitor_analyzer.name,
                msg=f"Asking the critic to critique the report",
            )
        )
        return CritiqueCompetitorsEvent(input=ctx.data["competitor_analysis_result"])

    @step()
    async def critique(
        self, ctx: Context, ev: CritiqueCompetitorsEvent, report_critic: FunctionCallingAgent
    ) -> ReportEvent:
        result = await self.run_agent(ctx, report_critic,
            f"""We are currently researching this task: {ctx.data['task']}
            We have researched and analyzed the competitors, and created this report draft: {ev.input}
            Please critique the report and provide actionable feedback for improvement."""
        )
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=report_critic.name,
                msg=f"Completed report critique: {result.response.message.content}",
            )
        )
        parser = JsonValidationHelper(CompetitorReportCritique, Settings.llm)
        parsed_response = await parser.validate_and_fix(result.response.message.content)
        
        if not parsed_response:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=report_critic.name,
                    msg=f"No valid JSON content found in the response",
                )
            )
            return ReportEvent(input=result.response.message.content)
        
        if parsed_response.satisfied:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=report_critic.name,
                    msg=f"Critic is satisfied with the report, moving on to generate the final report",
                )
            )
            return ReportEvent(input=ctx.data["competitor_analysis_result"])
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=report_critic.name,
                msg=f"Critic is not satisfied with the report, refining the report based on the feedback",
            )
        )
        return AnalyzeCompetitorsEvent(input=result.response.message.content)
    
    @step()
    async def report(
        self, ctx: Context, ev: ReportEvent, reporter: FunctionCallingAgent
    ) -> StopEvent:
        try:
            prompt = dedent(f"""
                We are currently researching this task: {ctx.data['task']}
                We have completed researching, analyzing and critiquing the competitors.
                Here is the final report: {ev.input}
            """)
            result: AgentRunResult = await self.run_agent(
                ctx, reporter, prompt
            )
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=reporter.name,
                    msg=f"Completed report creation: {result.response.message.content}",
                )
            )
            
            # Save all agent responses and sources so we can use them for RAG chat later
            initial_search_results = '\n'.join(ctx.data.get('initial_search_results', []))
            refined_search_results = '\n'.join(ctx.data.get('refined_search_results', []))
            write_file(
                content=dedent(f"""
                    # Competitor analysis activity
                    
                    ### Task
                    {ctx.data["task"]}
                    
                    ### Competitors
                    We found the following competitors:
                    {ctx.data["competitor_names"]}
                    
                    ### Initial research
                    We reranked and deduplicated the competitors based on their relevance to the task, and did more research on them. Here are their details:
                    {initial_search_results}
                    
                    ### Refined research
                    For more promising competitors, we did more research and here are their details:
                    {refined_search_results}
                    
                    ### Report
                    Then we synthesized the information and created this report:
                    {ctx.data["competitor_analysis_result"]}
                    
                    ### Sources
                    We used the following sources to compile the report:
                    {ctx.data["sources"]}
                """),
                file_name="report.txt",
                session_id=self.session_id,
            )
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=reporter.name,
                    msg=f"Saved report to report.txt",
                )
            )
            
            return StopEvent(result=result)
        except Exception as e:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=reporter.name,
                    msg=f"Error creating a report: {e}",
                )
            )
            return StopEvent(result=None)
    
    async def run_agent(self, ctx: Context, agent: FunctionCallingAgent, input: str) -> AgentRunResult:
        try:
            handler = agent.run(input=input, streaming=False)
            async for event in handler.stream_events():
                if type(event) is not StopEvent:
                    ctx.write_event_to_stream(event)
            return await handler
        except Exception as e:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=agent.name,
                    msg=f"Error running agent: {str(e)}",
                )
            )
            raise
    
    async def _generate_search_queries(self, task: str, chat_history: List[ChatMessage], number_of_queries: int = 5) -> List[str]:
        prompt_template = PromptTemplate(
            dedent("""
                ### Base Instructions
                You are an agent that thinks step by step and uses tools to satisfy the user's request. You first make a plan and execute it step by step through an observation - reason - action loop. In your responses, you always include all reasoning before taking an action or concluding.
                
                ### Instructions
                You are an expert at generating effective search queries to find competitors and similar products. Your goal is to create a diverse set of search queries that will help uncover both direct and indirect competitors.

                var NUMBER_OF_QUERIES={number_of_queries}
                
                For the given product idea, generate NUMBER_OF_QUERIES different search queries that:
                1. Use different terminology and approaches:
                a) direct competitor queries:
                    - Use formats like "X product", "X startup", "X app"
                    - Vary the terminology to capture different descriptions
                    - Think of alternative queries to find products that also solve the same problem
                    - Example: "ai sales email writer agent", "sales email automation tool", "email copilot app"
                b) general tool/software query:
                    - Use SEO-friendly terms like "tool", "software", "platform"
                    - Example: "sales email automation software"
                c) "best tools" overview query:
                    - Use format "best X tools" or "top X solutions"
                    - Example: "best ai sales email tools"

                2. Consider various angles depending on the product idea:
                - Autonomous/AI-driven solutions
                - Copilot/assistant approaches
                - Traditional software solutions
                - Emerging startups
                - Enterprise solutions

                ### Output
                Return a JSON array of NUMBER_OF_QUERIES search queries, each query should be a string.
                
                For example: 
                Input: "AI sales email writer"
                Output: ["ai sales email writer", "ai sales email automation", "ai sales email copilot", "autonomous sales email agent", "best ai tools for sales email writer"]
                Notice how i'm using different keywords to find similar products using different appraoches, from copilots to autonomous agents to best tools in the space.
                
                -----------------------------------------------------------------------
                
                ### Chat history:
                {chat_history}

                ### Task:
                {task}
                
                ### Output
            """)
        )

        prompt = prompt_template.format(task=task, chat_history=chat_history, number_of_queries=number_of_queries)
        output = await Settings.llm.acomplete(prompt)
        json_content = extract_json_from_response(output.text.strip())
        return json_content

    async def _deduplicate_and_rank_competitors(self, competitors: List[CompetitorInfo], task: str, n: int = 4) -> List[CompetitorInfo]:
        if len(competitors) == 0:
            return []
        
        prompt_template = PromptTemplate(
            dedent("""
                ### Instructions
                You are an expert at analyzing and ranking competitors. Your task is to:
                1. Remove duplicate competitors (same company listed multiple times)
                2. Rank the competitors based on their relevance to our product idea
                3. Return only the top {n} most relevant competitors

                Rank based on:
                - How directly they compete with our product idea
                - Market presence and traction
                - Feature overlap
                - Target audience similarity

                ### Product Idea
                {task}

                ### Competitors Found
                {competitors}

                ### Output Format
                Return a JSON array of the top {n} competitors, maintaining their original data structure.
                Only return the JSON array, no explanation needed.
                
                ### Reranked and deduplicated competitors output:
            """)
        )

        competitors_json = [comp.model_dump() for comp in competitors]
        
        prompt = prompt_template.format(
            task=task,
            competitors=competitors_json,
            n=n
        )
        
        output = await Settings.llm.acomplete(prompt)
        json_array = extract_json_from_response(output.text.strip())
        res = [CompetitorInfo.model_validate(comp) for comp in json_array]
        print(res)
        return res


def create_competitor_analysis(session_id: str, chat_history: List[ChatMessage], email: str | None = None, **kwargs):
    workflow = CompetitorAnalysisWorkflow(
        session_id=session_id,
        timeout=600,
        chat_history=chat_history,
    )
    
    competitor_analyzer = create_competitor_analyzer(chat_history)
    report_critic = create_report_critic(chat_history)
    reporter = create_reporter(chat_history, email)
    
    workflow.add_workflows(
        competitor_analyzer=competitor_analyzer,
        report_critic=report_critic,
        reporter=reporter,
    )
    
    return workflow