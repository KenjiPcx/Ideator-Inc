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
import HowToUseModal from "./components/how-to-use-modal";

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
  const [sessionId, _] = useState<string>(uuidv4());
  const { backend } = useClientConfig();
  const [requestData, setRequestData] = useState<any>();
  const [userEmail, setUserEmail] = useState<string>("");
  const [refinedIdea, setRefinedIdea] = useState<RefinedIdea | null>(null);
  const [isIdeaValidated, setIsIdeaValidated] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<
    keyof typeof stores | null
  >(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [previousAgentEventCount, setPreviousAgentEventCount] = useState(0);
  const [startedResearching, setStartedResearching] = useState(false);
  const [canChatWithAssistant, setCanChatWithAssistant] = useState(false);
  const [showHowToUse, setShowHowToUse] = useState(true);

  const {
    messages,
    setMessages,
    input,
    setInput,
    append,
    handleInputChange,
    handleSubmit,
    isLoading,
  } = useChat({
    id: sessionId,
    api: !isIdeaValidated
      ? "/api/validate"
      : selectedAgent !== "Research Assistant"
        ? `${backend}/api/chat`
        : `${backend}/api/chat/qna`,
    maxSteps: isIdeaValidated ? 1 : 5,
    headers: {
      "Content-Type": "application/json",
    },
    body: {
      data: requestData,
      email: userEmail,
      sessionId: sessionId,
    },
    sendExtraMessageFields: true,
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
        startResearch();
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
    handleSubmit(e);
  };

  useEffect(() => {
    console.log(messages);
  }, [messages]);

  // useEffect(() => {
  //   setIsIdeaValidated(true);
  //   setRefinedIdea(refinedIdea);
  //   console.log(sessionId);
  // }, []);

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
        console.log("Adding event to store", event);
        const store = stores[event.workflowName];
        if (store) {
          store.getState().addEvent(event);
        }
      });

      // Update the previous count
      setPreviousAgentEventCount(lastMessage.annotations.length);
    }
  }, [messages, previousAgentEventCount]);

  useEffect(() => {
    if (startedResearching && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      // Check if the last message indicates research completion
      // You might want to adjust this condition based on your specific needs
      if (
        lastMessage.role === "assistant" &&
        lastMessage.annotations?.length &&
        lastMessage.annotations.length > 10
      ) {
        setCanChatWithAssistant(true);
      }
    }
  }, [messages, startedResearching]);

  useEffect(() => {
    if (isIdeaValidated) {
      setIsModalOpen(false);
      setSelectedAgent(null);
    }
  }, [isIdeaValidated]);

  const startResearch = () => {
    append({
      role: "user",
      content: `Start research on the user's idea: \n${JSON.stringify(refinedIdea)}`,
    });
    setStartedResearching(true);
    alert("Research started");
  };

  const setDemoIdea = () => {
    setRefinedIdea(refinedIdeaTest);
    setIsIdeaValidated(true);
  };

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-gray-900 to-gray-800 flex flex-col">
      <Header setUserEmail={setUserEmail} />

      <div className="grid grid-cols-4 gap-8 flex-grow mt-8 rounded-lg">
        {/* Main Agents */}
        <AgentGrid
          name="Research Manager"
          role="Helps refine and validate startup ideas and then starts the research process"
          avatar="/avatars/idea_validator.png"
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
          role="Answers questions about research findings (Only available when research is complete)"
          avatar="/avatars/product_manager.png"
          isSelected={selectedAgent === "Research Assistant"}
          onClick={() => {
            if (canChatWithAssistant) {
              setSelectedAgent("Research Assistant");
              setIsModalOpen(true);
            }
          }}
          position={{ x: 3, y: 0 }}
          canChat={canChatWithAssistant}
        />

        {/* Research Teams */}
        {RESEARCH_TEAMS.map((team, i) => (
          <AgentGrid
            key={team.name}
            {...team}
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

      <div className="fixed bottom-8 right-8 absolute flex flex-col gap-2">
        {isIdeaValidated && !startedResearching && (
          <div className="group/research relative">
            <Button
              onClick={startResearch}
              className="rounded-full px-6 py-5 shadow-lg hover:shadow-xl transition-all flex items-center justify-center bg-green-600 hover:bg-green-700 animate-pulse"
            >
              Start Research
            </Button>
            <div className="absolute bottom-full right-0 mb-2 opacity-0 group-hover/research:opacity-100 transition-opacity duration-200">
              <div className="bg-gray-900 text-white text-sm py-1 px-2 rounded shadow-lg whitespace-nowrap">
                Begin AI-powered research process
              </div>
            </div>
          </div>
        )}
        {!refinedIdea && (
          <div className="group/demo relative">
            <Button
              onClick={setDemoIdea}
              className={`rounded-full px-6 py-3 shadow-lg hover:shadow-xl transition-all flex items-center justify-center ${
                startedResearching
                  ? "bg-blue-800 hover:bg-blue-900"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              Click for Demo Idea
            </Button>
            <div className="absolute bottom-full right-0 mb-2 opacity-0 group-hover/demo:opacity-100 transition-opacity duration-200">
              <div className="bg-gray-900 text-white text-sm py-1 px-2 rounded shadow-lg whitespace-nowrap">
                Start Research Process with Sample Idea
              </div>
            </div>
          </div>
        )}
      </div>

      <HowToUseModal 
        isOpen={showHowToUse} 
        onClose={() => setShowHowToUse(false)}
      />
    </main>
  );
}
