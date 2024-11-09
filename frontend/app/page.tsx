"use client";

import { useChat } from "ai/react";
import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import AgentGrid from "./components/agent-grid";
import AgentModal from "./components/agent-modal";
import Header from "./components/header";
import IdeaDisplay, { RefinedIdea } from "./components/idea-display";
import { Button } from "./components/ui/button";
import {
  AgentEventData,
  getAnnotationData,
  MessageAnnotation,
  MessageAnnotationType,
} from "./components/ui/chat";
import { useClientConfig } from "./components/ui/chat/hooks/use-config";
import { RESEARCH_TEAMS } from "./lib/research-team";
import { stores } from "./stores/agentStore";

const refinedIdeaTest = {
  name: "Ikigai Navigator",
  product_summary:
    "An AI assistant that simplifies the Ikigai exercise, guiding users through the process of self-discovery and life planning by asking tough questions and providing insights, ultimately transforming into a productivity app that helps users plan and achieve their goals.",
  problem_statement:
    "Many individuals, especially those starting their careers, feel lost and overwhelmed when it comes to planning their life and career paths. The traditional Ikigai exercise can be daunting and complex, leading to procrastination and fear of commitment.",
  product_idea:
    "An AI-driven platform that guides users through the Ikigai exercise in a conversational manner, helping them fill out the Ikigai diagram by asking relevant questions and providing suggestions based on their responses. After completing the exercise, the platform evolves into a productivity app that assists users in setting and tracking their goals.",
  unique_value_proposition:
    "Combines the introspective nature of the Ikigai exercise with the interactive support of an AI assistant, making the process less intimidating and more engaging, while also providing ongoing productivity support.",
  user_story:
    "As a young professional feeling lost in my career, I want to use an AI assistant to help me navigate the Ikigai exercise so that I can discover my purpose and create a structured plan for my life and goals.",
  how_it_works:
    "Users interact with the AI assistant, which prompts them with questions related to the four areas of the Ikigai diagram. As users respond, the AI fills in the diagram and offers insights. Once the exercise is complete, the app transitions into a productivity tool that helps users set and track their goals, providing regular reflections and planning assistance.",
  target_users:
    "Young professionals, recent graduates, and individuals seeking clarity in their life and career paths.",
};

export default function Home() {
  const [sessionId] = useState<string>(uuidv4());
  const { backend } = useClientConfig();
  const [requestData, setRequestData] = useState<any>();
  const [userEmail, setUserEmail] = useState<string>("");
  const [refinedIdea, setRefinedIdea] = useState<RefinedIdea | null>(
    refinedIdeaTest,
  );
  const [isIdeaValidated, setIsIdeaValidated] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<
    keyof typeof stores | null
  >(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [previousAgentEventCount, setPreviousAgentEventCount] = useState(0);

  const {
    messages,
    input,
    setInput,
    append,
    handleInputChange,
    handleSubmit,
    isLoading,
  } = useChat({
    id: sessionId,
    api: isIdeaValidated ? `${backend}/api/chat` : "/api/validate",
    headers: {
      "Content-Type": "application/json",
    },
    body: {
      data: requestData,
      email: userEmail,
      sessionId: sessionId,
    },
    sendExtraMessageFields: true,
    maxSteps: isIdeaValidated ? 1 : 3,
    onToolCall: async ({ toolCall }) => {
      const { toolName, args } = toolCall;
      if (toolName === "update_idea") {
        console.log("updated");
        console.log(args);
        setRefinedIdea(args as RefinedIdea);
        return "Idea updated successfully";
      }
      if (toolName === "confirm_idea") {
        console.log("confirmed");
        setIsIdeaValidated(true);
        return "Idea confirmed";
      }
      if (toolName === "start_research") {
        console.log("started research");
        return "Research started";
      }
    },
    onError: (error: unknown) => {
      if (!(error instanceof Error)) throw error;
      const message = JSON.parse(error.message);
      alert(message.detail);
    },
  });

  const handleAgentSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setPreviousAgentEventCount(0);
    if (messages.length === 0) {
      window.history.pushState({}, "", `/research/${sessionId}`);
    }
    handleSubmit(e);
  };

  // useEffect(() => {
  //   console.log(stores["Idea Validator"].getState().messages);
  // }, [input]);

  useEffect(() => {
    setIsIdeaValidated(true);
    setRefinedIdea(refinedIdea);
    console.log(sessionId);
  }, []);

  useEffect(() => {
    console.log(messages);
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) return;
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage.annotations) return;
    const annotations = lastMessage.annotations as MessageAnnotation[];
    const agentEventData = getAnnotationData<AgentEventData>(
      annotations,
      MessageAnnotationType.AGENT_EVENTS,
    );

    if (agentEventData.length > previousAgentEventCount) {
      // Get only the new annotations
      const newAgentEvents = agentEventData.slice(previousAgentEventCount);

      // Distribute each new annotation to the correct store
      newAgentEvents.forEach((event: AgentEventData) => {
        // Find the correct store based on the agent name
        console.log("Adding event to store", event.workflowName);
        const store = stores[event.workflowName];
        if (store) {
          store.getState().addEvent(event);
        }
      });

      // Update the previous count
      setPreviousAgentEventCount(lastMessage.annotations.length);
    }
  }, [messages, previousAgentEventCount]);

  const startResearch = () => {
    setInput(
      `Start research on the user's idea: \n${JSON.stringify(refinedIdea)}`,
    );
    setTimeout(() => {
      console.log("Starting research successfully");
      handleSubmit();
    }, 1000);
  };

  useEffect(() => {
    // If the number of messages is even, then its the assistant responding
    if (messages.length > 0 && messages.length % 2 === 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.annotations) {
        console.log(lastMessage.annotations);
      }
    }
  }, [messages]);

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-gray-900 to-gray-800 flex flex-col">
      <Header setUserEmail={setUserEmail} />

      <Button onClick={startResearch}>Start Research</Button>
      <div className="grid grid-cols-4 gap-8 flex-grow mt-8 rounded-lg">
        {/* Main Agents */}
        <AgentGrid
          name="Research Manager"
          role="Helps refine and validate startup ideas and then starts the research process"
          avatar="/avatars/idea_validator.png"
          isActive={!isIdeaValidated}
          isSelected={selectedAgent === "Research Manager"}
          isModalOpen={isModalOpen}
          onClick={() => {
            setSelectedAgent("Research Manager");
            setIsModalOpen(true);
          }}
          position={{ x: 0, y: 0 }}
          canChat={true}
        />

        <div className="col-span-2">
          <IdeaDisplay idea={refinedIdea} isValidated={isIdeaValidated} />
        </div>

        <AgentGrid
          name="Research Assistant"
          role="Answers questions about research findings"
          avatar="/avatars/product_manager.png"
          isActive={isIdeaValidated}
          isLocked={!isIdeaValidated}
          isSelected={selectedAgent === "Research Assistant"}
          onClick={() => {
            setSelectedAgent("Research Assistant");
            setIsModalOpen(true);
          }}
          position={{ x: 3, y: 0 }}
          canChat={true}
        />

        {/* Research Teams */}
        {RESEARCH_TEAMS.map((team, i) => (
          <AgentGrid
            key={team.name}
            {...team}
            isActive={isIdeaValidated}
            isLocked={!isIdeaValidated}
            isSelected={selectedAgent === team.name}
            isModalOpen={isModalOpen}
            onClick={() => {
              setSelectedAgent(team.name);
              setIsModalOpen(true);
            }}
            position={{ x: i % 4, y: Math.floor(i / 4) + 1 }}
          />
        ))}
      </div>

      {/* Agent Modal */}
      {selectedAgent && (
        <AgentModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedAgent(null);
          }}
          agent={{
            name: selectedAgent,
            role:
              RESEARCH_TEAMS.find((t) => t.name === selectedAgent)?.role || "",
            canChat: ["Research Manager", "Research Assistant"].includes(
              selectedAgent,
            ),
          }}
          messages={messages}
          input={input}
          handleInputChange={handleInputChange}
          handleSubmit={handleAgentSubmit}
          isLoading={isLoading}
          setInput={setInput}
          append={append}
          requestData={requestData}
          setRequestData={setRequestData}
        />
      )}
    </main>
  );
}
