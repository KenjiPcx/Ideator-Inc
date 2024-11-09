import { Message } from 'ai';

export interface ChatMessage extends Message {
  agentName: string;
  timestamp: Date;
} 