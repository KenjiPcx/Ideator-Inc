"use client";

import { useChat } from "ai/react";
import { useState, useEffect } from "react";
import { ChatInput, ChatMessages } from "./ui/chat";
import { useClientConfig } from "./ui/chat/hooks/use-config";
import { v4 as uuidv4 } from 'uuid';

interface RefinedIdea {
  problem_statement: string;
  product_idea: string;
  unique_value_proposition: string;
  user_story: string;
  how_it_works: string;
  target_users: string;
}

interface ChatSectionProps {
  sessionId?: string;
  onFirstMessage?: (sessionId: string) => void;
}

export default function ChatSection({ sessionId: providedSessionId, onFirstMessage }: ChatSectionProps) {
  const { backend } = useClientConfig();
  const [requestData, setRequestData] = useState<any>();
  const [userEmail, setUserEmail] = useState<string>("");
  const [localSessionId, setLocalSessionId] = useState<string>(providedSessionId || "");
  const [refinedIdea, setRefinedIdea] = useState<RefinedIdea | null>(null);
  const [isIdeaValidated, setIsIdeaValidated] = useState(false);
  const [isResearchMode, setIsResearchMode] = useState(false);

  const {
    messages,
    input,
    isLoading,
    handleSubmit,
    handleInputChange,
    reload,
    stop,
    append,
    setInput,
  } = useChat({
    id: localSessionId,
    body: { 
      data: requestData,
      email: userEmail,
      sessionId: localSessionId,
      mode: isResearchMode ? 'research' : 'validation'
    },
    api: isResearchMode ? `${backend}/api/chat` : '/api/validate',
    headers: {
      "Content-Type": "application/json",
    },
    maxSteps: 5,
    onToolCall: async ({ toolCall }) => {
      if (toolCall.toolName === 'update_idea') {
        setRefinedIdea(toolCall.args as RefinedIdea);
        return 'Idea updated successfully';
      }
      if (toolCall.toolName === 'confirm_idea') {
        setIsIdeaValidated(true);
        return 'Idea confirmed';
      }
    },
    onError: (error: unknown) => {
      if (!(error instanceof Error)) throw error;
      const message = JSON.parse(error.message);
      alert(message.detail);
    },
    sendExtraMessageFields: true,
  });

  const handleFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!providedSessionId && messages.length === 0) {
      const newSessionId = uuidv4();
      setLocalSessionId(newSessionId);
      onFirstMessage?.(newSessionId);
      setTimeout(() => {
        handleSubmit(e);
      }, 1000);
    } else {
      handleSubmit(e);
    }
  };

  const startResearch = () => {
    setIsResearchMode(true);
    append({
      role: 'system',
      content: 'Starting research process with validated idea...',
    });
    handleSubmit(new Event('submit') as any);
  };

  return (
    <div className="space-y-4 w-full h-full flex flex-col">
      <div className="w-full mb-4">
        <form className="flex gap-2">
          <input
            type="email"
            value={userEmail}
            onChange={(e) => setUserEmail(e.target.value)}
            placeholder="Enter your email for the report"
            className="flex-1 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white/80"
            required
          />
        </form>
      </div>

      {refinedIdea && (
        <div className="bg-white/80 p-4 rounded-lg shadow">
          <h3 className="font-bold mb-2">Refined Idea</h3>
          <div className="space-y-2">
            <p><strong>Problem:</strong> {refinedIdea.problem_statement}</p>
            <p><strong>Solution:</strong> {refinedIdea.product_idea}</p>
            <p><strong>Value Prop:</strong> {refinedIdea.unique_value_proposition}</p>
            {/* Add other fields as needed */}
          </div>
          {isIdeaValidated && !isResearchMode && (
            <button
              onClick={startResearch}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Start Research
            </button>
          )}
        </div>
      )}

      <ChatMessages
        messages={messages}
        isLoading={isLoading}
        reload={reload}
        stop={stop}
        append={append}
      />
      <ChatInput
        input={input}
        handleSubmit={handleFormSubmit}
        handleInputChange={handleInputChange}
        isLoading={isLoading}
        messages={messages}
        append={append}
        setInput={setInput}
        requestParams={{ params: requestData, email: userEmail }}
        setRequestData={setRequestData}
      />
    </div>
  );
}
