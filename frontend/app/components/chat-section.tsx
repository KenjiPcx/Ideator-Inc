"use client";

import { useChat } from "ai/react";
import { useState, useEffect } from "react";
import { ChatInput, ChatMessages } from "./ui/chat";
import { useClientConfig } from "./ui/chat/hooks/use-config";
import { v4 as uuidv4 } from 'uuid';

interface ChatSectionProps {
  sessionId?: string;
  onFirstMessage?: (sessionId: string) => void;
}

export default function ChatSection({ sessionId: providedSessionId, onFirstMessage }: ChatSectionProps) {
  const { backend } = useClientConfig();
  const [requestData, setRequestData] = useState<any>();
  const [userEmail, setUserEmail] = useState<string>("");
  const [localSessionId, setLocalSessionId] = useState<string>(providedSessionId || "");

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
    },
    api: `${backend}/api/chat`,
    headers: {
      "Content-Type": "application/json",
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
