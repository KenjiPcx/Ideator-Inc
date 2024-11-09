import { stores } from "../stores/agentStore";

export const RESEARCH_TEAMS: {
  name: keyof typeof stores;
  role: string;
  avatar: string;
  canChat: boolean;
}[] = [
  {
    name: "Competitor Analysis",
    role: "Analyzes market competitors and their strategies",
    avatar: "/avatars/competitor_analyst.png",
    canChat: false,
  },
  {
    name: "Market Research",
    role: "Studies market size, trends, and opportunities",
    avatar: "/avatars/market_analyst.png",
    canChat: false,
  },
  {
    name: "Customer Insights",
    role: "Analyzes customer needs and behaviors",
    avatar: "/avatars/customer_insight.png",
    canChat: false,
  },
  {
    name: "Online Trends",
    role: "Tracks digital trends and online presence",
    avatar: "/avatars/online_trends.png",
    canChat: false,
  },
  {
    name: "Podcast Creation",
    role: "Creates engaging podcast content",
    avatar: "/avatars/podcaster.png",
    canChat: false,
  },
  {
    name: "Executive Summarizer",
    role: "Creates a concise executive summary of the idea",
    avatar: "/avatars/executive_summarizer.png",
    canChat: false,
  },
  {
    name: "Financial Report Workflow",
    role: "Creates a financial report",
    avatar: "/avatars/financial_report.png",
    canChat: false,
  },
];
