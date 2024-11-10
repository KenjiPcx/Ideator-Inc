import { useEffect, useState } from "react";
import { stores } from "../stores/agentStore";
import { AgentEventData } from "./ui/chat";
import { motion, AnimatePresence } from "framer-motion";

export interface AgentGridProps {
  name: keyof typeof stores;
  role: string;
  avatar: string;
  isSelected: boolean;
  isModalOpen?: boolean;
  onClick: () => void;
  position: { x: number; y: number };
  canChat: boolean;
}

export default function AgentGrid({
  name,
  role,
  avatar,
  isSelected,
  isModalOpen = false,
  onClick,
  position,
  canChat,
}: AgentGridProps) {
  const events = stores[name]((state) => state.events);
  const [latestEvent, setLatestEvent] = useState<AgentEventData | null>(null);
  const testEvent = {
    agent: "Test Agent",
    text: "This is a test event",
  };
  // Compute active/locked states based on events
  const isActive = events.length > 0;
  const isLocked = !canChat && !isActive;

  useEffect(() => {
    const store = stores[name];
    if (!store) return;

    // Subscribe to store changes
    const unsubscribe = store.subscribe((state) => {
      const events = state.events;
      if (events && events.length > 0) {
        const lastEvent = events[events.length - 1];
        setLatestEvent(lastEvent);
        // Auto-hide notification after 5 seconds
        setTimeout(() => setLatestEvent(null), 5000);
      }
    });

    return () => unsubscribe();
  }, [name]);

  return (
    <div
      className={`
        relative p-4 rounded-lg transition-all duration-300
        ${isLocked ? "bg-gray-800 opacity-50 cursor-not-allowed" : "bg-gray-700 cursor-pointer hover:bg-gray-600"}
        ${isSelected ? "ring-2 ring-blue-500" : ""}
        ${isActive ? "animate-pulse" : ""}
      `}
      onClick={isLocked ? undefined : onClick}
      style={{
        gridColumn: position.x + 1,
        gridRow: position.y + 1,
      }}
    >
      {/* Avatar */}
      <div className="flex items-center justify-center mb-4">
        <div className="relative w-24 h-24">
          <img src={avatar} alt={name} className="rounded-full" />
          {isLocked && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-full">
              <svg
                className="w-8 h-8 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          )}
        </div>
      </div>

      {/* Agent Info */}
      <div className="text-center">
        <h3 className="text-lg font-bold text-white mb-1">{name}</h3>
        <p className="text-sm text-gray-300">{role}</p>
      </div>

      {/* Status Indicator */}
      <div
        className={`absolute top-2 right-2 w-3 h-3 rounded-full ${
          isActive ? "bg-green-500" : "bg-gray-500"
        }`}
      />

      {/* Notification popup - updated positioning */}
      <AnimatePresence>
        {latestEvent && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute left-[20%] bottom-5"
          >
            <div className="bg-black/80 text-white p-3 rounded-lg shadow-lg max-w-xs">
              <p className="text-sm line-clamp-2">
                {latestEvent.agent}: {latestEvent.text}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
