/* ---- Poll types ---- */

export interface PollOption {
  id: string;
  text: string;
}

export interface PollSummary {
  pollId: string;
  title: string;
  question: string;
  totalVotes: number;
  status: 'open' | 'closed';
  createdBy: string;
  createdByName: string;
  createdAt: string;
}

export interface Poll extends PollSummary {
  options: PollOption[];
  counts: Record<string, number>;
  hasVoted: boolean;
  userChoice: string | null;
}

export interface PollResultOption {
  id: string;
  text: string;
  count: number;
  percentage: number;
}

export interface PollResults {
  pollId: string;
  title: string;
  question: string;
  status: 'open' | 'closed';
  totalVotes: number;
  options: PollResultOption[];
  userChoice: string | null;
}

/* ---- Request types ---- */

export interface CreatePollPayload {
  title: string;
  question: string;
  options: string[];
}

export interface CastVotePayload {
  optionId: string;
}

/* ---- Error types ---- */

export interface ApiErrorBody {
  code: string;
  message: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}
