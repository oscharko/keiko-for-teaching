export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  role: MessageRole;
  content: string;
}

export interface DataPoints {
  text: string[];
  images: string[];
  citations: string[];
}

export interface Thought {
  title: string;
  description: string;
}

export interface ResponseContext {
  data_points: DataPoints;
  thoughts?: Thought[];
  followup_questions?: string[];
}

export interface ChatRequest {
  messages: Message[];
  context?: {
    overrides?: ChatOverrides;
  };
  session_state?: unknown;
}

export interface ChatOverrides {
  retrieval_mode?: 'hybrid' | 'text' | 'vectors';
  semantic_ranker?: boolean;
  semantic_captions?: boolean;
  top?: number;
  temperature?: number;
  prompt_template?: string;
  exclude_category?: string;
  suggest_followup_questions?: boolean;
  use_oid_security_filter?: boolean;
  use_groups_security_filter?: boolean;
  use_rag?: boolean;
  stream?: boolean;
}

export interface ChatResponse {
  message: Message;
  context: ResponseContext;
  session_state?: unknown;
}

export interface ChatStreamEvent {
  delta?: Partial<Message>;
  context?: ResponseContext;
  done: boolean;
  error?: string;
}

