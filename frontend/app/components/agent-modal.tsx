import { Message } from 'ai';
import { stores } from "../stores/agentStore";
import { ChatAgentEvents } from "./ui/chat/chat-message/chat-agent-events";
import ChatInput from './ui/chat/chat-input';
import ChatMessages from './ui/chat/chat-messages';

interface AgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent: {
    name: string;
    role: string;
    canChat: boolean;
  };
  messages: Message[];
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
  append?: (message: Message | Omit<Message, "id">) => Promise<string | undefined | null>;
  setInput?: React.Dispatch<React.SetStateAction<string>>;
  requestData?: any;
  setRequestData?: React.Dispatch<any>;
}

export default function AgentModal({ 
  isOpen, 
  onClose, 
  agent,
  ...props
}: AgentModalProps) {
  if (!isOpen) return null;

  const store = stores[agent.name as keyof typeof stores];
  const events = store?.getState().events || [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg w-[55vw] h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-5 py-3 border-b border-gray-700 flex justify-between items-center shrink-0">
          <div>
            <h3 className="text-xl font-bold text-white">{agent.name}</h3>
            <p className="text-sm text-gray-400">{agent.role}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto flex flex-col">
          {agent.canChat ? (
            <>
              <ChatMessages
                messages={props.messages}
                isLoading={props.isLoading}
                append={props.append}
              />
              <div className="p-4">
                <ChatInput
                  input={props.input}
                  handleInputChange={props.handleInputChange}
                  handleSubmit={props.handleSubmit}
                  isLoading={props.isLoading}
                  messages={props.messages}
                  append={props.append}
                  requestParams={{ params: props.requestData }}
                  setRequestData={props.setRequestData}
                  setInput={props.setInput}
                />
              </div>
            </>
          ) : (
            <div className="p-4">
              <ChatAgentEvents 
                data={events} 
                isFinished={false}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 