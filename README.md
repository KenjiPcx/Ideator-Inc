# Ideator-Inc

## Overview

Ideator Inc is an autonomous AI research agency that helps indie hackers validate and research their startup ideas. Think of it as having your own team of AI agents working together to gather essential market intelligence, competitor analysis, and customer insights.

**"Are you an indie hacker with too many ideas but not sure which one to pursue? Meet your new AI research team, ready to work for you right now."**

The research workflow is inspired by modern marketing methodologies popularized by Greg Isenberg, leveraging community platforms like Reddit to gather authentic market research and customer insights.

## Demo

Hear my pitch on the demo:

![Ideator Inc Demo](https://www.loom.com/share/4553e9b98ba143d3bc6895f286039703?sid=ff3ee1f0-181c-496a-8a0d-9f769cf2e5f6)

## How It Works

1. Share your startup idea with the Research Manager
2. AI helps refine and validate your concept
3. Multiple AI agents conduct parallel research across different areas
4. Monitor each agent's progress through an intuitive dashboard
5. Chat with the Research Assistant to understand the findings and insights
6. Get comprehensive research results to make informed decisions

## Key UX Contributions

This project introduces innovative UX patterns for multi-agent systems:

- **Top-down Management View**: Watch your AI team in action with a dashboard that visualizes each agent's activities in real-time
- **Transparent Decision Making**: Understand how agents reach their conclusions through a unique QnA system
- **Interactive Office Environment**: Experience a mock office setup where you can interact with different AI agents
- **Post-Research Interactions**: Chat with agents after their tasks are complete to dive deeper into their findings

## Output Quality

I have shared some examples of the output quality in the demo video. Judge for yourself.

## Technical Stack (NVIDIA LlamaIndex Hack)

This project leverages cutting-edge AI models and frameworks:

- **Base Model**: Meta's Llama-3.1-70B-Instruct for core inference
- **Embeddings**: NVIDIA NeMo Retriever (nvidia/nv-embedqa-mistral-7b-v2)
- **Framework**: NIM for efficient model deployment
- **Attempted**: NVIDIA NeMo Guardrails for structured output (deprecated due to version conflicts)

My NVIDIA account got rate limited, so you will have to unfortunately switch to a different model provider to get this running.

## Getting Started

There are dedicated README files for the frontend [frontend/README.md](./frontend/README.md) and backend [backend/README.md](./backend/README.md).

## Note from the Creator

This project serves as a proof of concept for multi-agent frameworks and their potential in automating research workflows. While it won't be actively maintained, it demonstrates the possibilities of AI agent collaboration and provides a reference implementation for building similar systems.

I'm planning to create courses on building multi-agent systems based on the learnings from this project. Feel free to use this as inspiration for your own AI agent implementations, particularly the UX patterns for managing and interacting with multiple agents.

The main contribution here is demonstrating how to create an intuitive interface for multi-agent systems, allowing users to both oversee operations and deeply understand agent decision-making processes.