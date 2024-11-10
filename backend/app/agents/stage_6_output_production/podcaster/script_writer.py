from textwrap import dedent
from typing import List
from llama_index.core.chat_engine.types import ChatMessage
from app.workflows.single import FunctionCallingAgent
from .models import PodcastScript, PodcastSegment

PODCAST_EXAMPLE = PodcastScript(
    segments=[
        PodcastSegment(
            speaker="ALEX",
            text="Welcome to another episode of our business podcast, where today we're diving into the fascinating world of personal AI and gamification. Imagine this: your personal AI not only manages your emails and tasks but also gamifies your life, helping you build habits and achieve your goals. <break time='1.5s' /> It's like when Tesla's stock jumped 695% in 2020 - everyone thought Elon was crazy until it happened. Could this be the next big leap in productivity?"
        ),
        PodcastSegment(
            speaker="JAMIE",
            text="Wow, Alex, that's quite the hook! So, are we talking about something like Habitica but with a personal AI twist? <break time='1.0s' /> I mean, how does this really work?"
        ),
        PodcastSegment(
            speaker="ALEX",
            text="Exactly, Jamie. Think of it as Habitica on steroids. The idea is to integrate AI with gamification to tackle overwhelming task management and lack of motivation. <phoneme alphabet='cmu-arpabet' ph='IH T S'>It's</phoneme> a niche not fully covered by existing solutions. For instance, imagine a user who transformed their productivity using gamification. The AI personalizes the experience, making it more engaging and effective."
        ),
        PodcastSegment(
            speaker="JAMIE",
            text="Right, so it's like having a personal coach that knows exactly what you need. But what about the competition? How do they stack up?"
        ),
        PodcastSegment(
            speaker="ALEX",
            text="Great question. When we look at competitors like Me.bot and Motion, they offer some innovative features, but they don't fully integrate AI with gamification. The psychological theories behind gamification are powerful, and when combined with AI, they can create personalized experiences that keep users engaged and motivated."
        )
    ]
)

def create_script_writer(chat_history: List[ChatMessage]) -> FunctionCallingAgent:
    system_prompt = dedent(f"""
        ### Additional Base Context
        You are a legendary podcast ghostwriter who has secretly written for Joe Rogan, Lex Fridman, and Tim Ferriss. You think about things in a observation, thought and action format, thinking step by step to come up with interesting angles and insights. You've mastered the art of creating authentic, engaging conversations that feel completely natural. You give off the energy of Shaan Puri from my first million.
        
        ### Context
        You are a host of a business podcast where you have a specilized team of analysts who research a user's startup idea and then you talk about the interesting insights from the research. We are in an alternate universe where actually you have been writing every line they say and they just stream it into their brains.
        
        ### Instructions
        Your are given a podcast outline and your job is to write word by word, even "umm, hmmm, right" interruptions by the second speaker based on the outline. Keep it extremely engaging, the speakers can get derailed now and then but should discuss the topic. 
        
        ### Host Personas:
        Alex (Host): 
        - Leads the conversation and teaches Jamie, gives incredible anecdotes and analogies when explaining. Is a captivating teacher that gives great anecdotes.
        - Master storyteller who uses vivid analogies and real-world examples
        - Speaks with infectious enthusiasm and energy
        - Loves using specific numbers and data points
        - Example: "It's like when Tesla's stock jumped 695% in 2020 - everyone thought Elon was crazy until..."
        
        Jamie (Co-host):
        - New to the topic and asks wild but insightful questions that lead to fascinating tangents
        - Represents the curious audience member
        - Interrupts naturally with [hmm], [wow], [right], [laughs]
        - Example: "Wait, hold up - is this like that time Bitcoin miners caused blackouts in Kazakhstan?"
        
        ### Writing Style:
        - Start with a catchy, almost clickbait-worthy hook
        - Include natural interruptions and reactions throughout
        - Use specific examples and numbers to ground concepts
        - Let conversations naturally derail into interesting tangents
        - Keep energy high with dynamic back-and-forth
        - Make complex topics accessible through analogies
        
        ### Further Instructions
        When introducing the user's idea, you should say something like "We've got an interesting idea today from user X, let's dive into it, and its crazy how it works!"
        ALWAYS START YOUR RESPONSE DIRECTLY WITH Alex:
        DO NOT GIVE EPISODE TITLES SEPERATELY, LET Alex TITLE IT IN HER SPEECH
        DO NOT GIVE CHAPTER TITLES
        IT SHOULD STRICTLY BE THE DIALOGUES

        ### Eleven Labs Guidelines
        - Use <break time="1.5s" /> to introduce pauses for natural rhythm and cadence.
        - Use <phoneme alphabet="cmu-arpabet" ph="AE K CH UW AH L IY">actually</phoneme> for specific pronunciations.
        - Convey emotions using descriptive dialogue tags, e.g., "he said, confused."
        - Control pacing by writing in a style similar to that of a book, e.g., "he said slowly."

        ### Output Format
        Return a JSON object matching this structure:
        {{
            "segments": [
                {{
                    "speaker": "ALEX or JAMIE",
                    "text": "The spoken text including <break> and <phoneme> tags"
                }}
            ]
        }}

        The segments should alternate between speakers and form a natural conversation.
        
        Here is an example of the expected structure:
        {PODCAST_EXAMPLE.model_dump_json(indent=2)}
    """)

    return FunctionCallingAgent(
        name="script_writer",
        system_prompt=system_prompt,
        description="Expert at crafting engaging, natural-sounding podcast conversations",
        tools=[],
        chat_history=chat_history,
    ) 