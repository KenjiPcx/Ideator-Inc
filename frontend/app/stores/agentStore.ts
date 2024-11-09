import { create } from "zustand";
import { AgentEventData } from "../components/ui/chat";
interface AgentStore {
  events: AgentEventData[];
  addEvent: (event: AgentEventData) => void;
  clearEvents: () => void;
}

const createAgentStore = () =>
  create<AgentStore>((set) => ({
    events: [],
    addEvent: (event) =>
      set((state) => ({
        events: [...state.events, event],
      })),
    clearEvents: () => set({ events: [] }),
  }));

export const stores = {
  "Financial Report Workflow": createAgentStore(),
  "Research Manager": createAgentStore(),
  "Research Assistant": createAgentStore(),
  "Competitor Analysis": createAgentStore(),
  "Market Research": createAgentStore(),
  "Customer Insights": createAgentStore(),
  "Online Trends": createAgentStore(),
  "Podcast Creation": createAgentStore(),
  "Executive Summarizer": createAgentStore(),
};
