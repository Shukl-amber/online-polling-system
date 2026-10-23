import { fetchAuthSession } from 'aws-amplify/auth';
import {
  ApiError,
  type ApiErrorBody,
  type CastVotePayload,
  type CreatePollPayload,
  type Poll,
  type PollResults,
  type PollSummary,
} from './types';

const API_URL = import.meta.env.VITE_API_URL as string;

async function getIdToken(): Promise<string> {
  const session = await fetchAuthSession();
  const token = session.tokens?.idToken?.toString();
  if (!token) {
    throw new ApiError(401, 'NO_TOKEN', 'Not authenticated');
  }
  return token;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await getIdToken();

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: token,
      ...options.headers,
    },
  });

  const body = await response.json();

  if (!response.ok) {
    const error = body.error as ApiErrorBody | undefined;
    throw new ApiError(
      response.status,
      error?.code ?? 'UNKNOWN',
      error?.message ?? 'An unexpected error occurred',
    );
  }

  return body as T;
}

/* ---- API functions ---- */

export async function createPoll(
  payload: CreatePollPayload,
): Promise<Poll> {
  return request<Poll>('/polls', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listPolls(): Promise<{ polls: PollSummary[] }> {
  return request<{ polls: PollSummary[] }>('/polls');
}

export async function getPoll(pollId: string): Promise<Poll> {
  return request<Poll>(`/polls/${pollId}`);
}

export async function castVote(
  pollId: string,
  payload: CastVotePayload,
): Promise<{ message: string; optionId: string }> {
  return request<{ message: string; optionId: string }>(
    `/polls/${pollId}/vote`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
}

export async function getResults(
  pollId: string,
): Promise<PollResults> {
  return request<PollResults>(`/polls/${pollId}/results`);
}

export async function closePoll(
  pollId: string,
): Promise<{ pollId: string; status: string; message: string }> {
  return request<{ pollId: string; status: string; message: string }>(
    `/polls/${pollId}/close`,
    { method: 'POST' },
  );
}
