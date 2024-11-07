from llama_index.core.workflow import Event
from typing import Dict, Any, List, Tuple


### High Level Events ###
class QnaWorkflowEvent(Event):
    '''
    Fired when the user has a question for the AI
    '''
    input: str

class ResearchWorkflowEvent(Event):
    '''
    Fired when the user has a research query
    '''
    input: str

### Initial Research Events ###
class StartResearchPipelineEvent(Event):
    '''
    Fired when the user has provided enough information to start the research pipeline
    '''
    input: str
    
class InitialResearchCompleteEvent(Event):
    '''
    Fired when the initial research is complete
    '''
    input: str

class CompetitorAnalysisFeedbackEvent(Event):
    '''
    Fired when the competitor analysis critique gives feedback
    '''
    input: str

class GetCompetitorAnalysisCritiqueEvent(Event):
    '''
    Fired when the competitor analysis agent needs feedback
    '''
    input: str

class GetCustomerInsightsCritiqueEvent(Event):
    '''
    Fired when the customer insights agent needs feedback
    '''
    input: str

class CustomerInsightsFeedbackEvent(Event):
    '''
    Fired when the customer insights critique gives feedback
    '''
    input: str

class GetOnlineTrendsCritiqueEvent(Event):
    '''
    Fired when the online trends agent needs feedback
    '''
    input: str

class OnlineTrendsFeedbackEvent(Event):
    '''
    Fired when the online trends critique gives feedback
    '''
    input: str

class MarketResearchFeedbackEvent(Event):
    '''
    Fired when the market research critique gives feedback
    '''
    input: str

class GetMarketResearchCritiqueEvent(Event):
    '''
    Fired when the market research agent needs feedback
    '''
    input: str

### Feasibility Research Events ###
class StartFeasibilityResearchEvent(Event):
    '''
    Fired when the user has provided enough information to start the feasibility research pipeline
    '''
    input: str

class FeasibilityCompleteEvent(Event):
    '''
    Fired when the feasibility research is complete
    '''
    input: str

class TechFeasibilityFeedbackEvent(Event):
    '''
    Fired when the tech feasibility critique gives feedback
    '''
    input: str

class GetTechFeasibilityCritiqueEvent(Event):
    '''
    Fired when the tech feasibility research agent needs feedback
    '''
    input: str

class FinanceFeasibilityFeedbackEvent(Event):
    '''
    Fired when the finance feasibility critique gives feedback
    '''
    input: str

class GetFinanceFeasibilityCritiqueEvent(Event):
    '''
    Fired when the finance feasibility research agent needs feedback
    '''
    input: str  

class OperationsFeasibilityFeedbackEvent(Event):
    '''
    Fired when the operations feasibility critique gives feedback
    '''
    input: str

class GetOperationsFeasibilityCritiqueEvent(Event):
    '''
    Fired when the operations feasibility research agent needs feedback
    '''
    input: str

class RiskAnalysisCompleteEvent(Event):
    '''
    Fired when the risk analysis is complete
    '''
    input: str

class GetRiskAnalysisCritiqueEvent(Event):
    '''
    Fired when the risk analysis agent needs feedback
    '''
    input: str

class SummarizeEverythingEvent(Event):
    '''
    Fired when all research is complete and that its time to summarize everything
    '''
    input: str

class GeneratePodcastEvent(Event):
    """Event to trigger podcast generation from research results"""
    research_results: Dict[str, Any]
    output_path: str = "./resources/final_podcast.mp3"

class CreatePodcastEvent(Event):
    """Event to trigger podcast creation"""
    input: str

class PodcastCreatedEvent(Event):
    """Event emitted when podcast is created"""
    summary: str
    podcast_transcript: str
    tts_ready_segments: List[Tuple[str, str]]