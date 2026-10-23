import '@testing-library/jest-dom/vitest';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PollDetailPage } from './PollDetailPage';
import * as api from '../../shared/api';
import { ApiError, type Poll, type PollResults } from '../../shared/types';

vi.mock('../../shared/api');

const mockPoll: Poll = {
  pollId: 'poll-123',
  title: 'Preferred Cloud Provider',
  question: 'Which cloud provider do you prefer for serverless?',
  options: [
    { id: 'opt-1', text: 'AWS' },
    { id: 'opt-2', text: 'GCP' },
    { id: 'opt-3', text: 'Azure' },
  ],
  counts: { 'opt-1': 10, 'opt-2': 5, 'opt-3': 2 },
  totalVotes: 17,
  status: 'open',
  createdBy: 'user-creator',
  createdByName: 'Creator User',
  createdAt: '2026-10-23T10:00:00Z',
  hasVoted: false,
  userChoice: null,
};

const mockResults: PollResults = {
  pollId: 'poll-123',
  title: 'Preferred Cloud Provider',
  question: 'Which cloud provider do you prefer for serverless?',
  totalVotes: 18,
  status: 'open',
  userChoice: 'opt-1',
  options: [
    { id: 'opt-1', text: 'AWS', count: 11, percentage: 61.1 },
    { id: 'opt-2', text: 'GCP', count: 5, percentage: 27.8 },
    { id: 'opt-3', text: 'Azure', count: 2, percentage: 11.1 },
  ],
};

function renderComponent() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/polls/poll-123']}>
        <Routes>
          <Route path="/polls/:id" element={<PollDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('PollDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders poll options and allows casting a vote', async () => {
    vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
    vi.mocked(api.castVote).mockResolvedValue({ message: 'Vote recorded', optionId: 'opt-1' });
    vi.mocked(api.getResults).mockResolvedValue(mockResults);

    renderComponent();

    expect(await screen.findByText('Preferred Cloud Provider')).toBeInTheDocument();
    expect(screen.getByText('Which cloud provider do you prefer for serverless?')).toBeInTheDocument();

    // Select AWS radio button
    const radioAws = screen.getByLabelText('AWS');
    fireEvent.click(radioAws);

    // Vote button should now be enabled
    const voteBtn = screen.getByRole('button', { name: /submit vote/i });
    expect(voteBtn).not.toBeDisabled();
    fireEvent.click(voteBtn);

    await waitFor(() => {
      expect(api.castVote).toHaveBeenCalledWith('poll-123', { optionId: 'opt-1' });
    });
  });

  it('renders horizontal result bars with count and percentage in tabular numerals', async () => {
    const alreadyVotedPoll: Poll = { ...mockPoll, hasVoted: true, userChoice: 'opt-1' };
    vi.mocked(api.getPoll).mockResolvedValue(alreadyVotedPoll);
    vi.mocked(api.getResults).mockResolvedValue(mockResults);

    renderComponent();

    // Results panel should display
    expect(await screen.findByText('Results')).toBeInTheDocument();
    expect(await screen.findByText(/total:\s*18\s*votes/i)).toBeInTheDocument();

    // Verify percentage rendering
    expect(screen.getByText(/61.1%/)).toBeInTheDocument();
    expect(screen.getByText(/27.8%/)).toBeInTheDocument();
  });

  it('handles 409 duplicate vote error calmly without crashing', async () => {
    vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
    vi.mocked(api.castVote).mockRejectedValue(
      new ApiError(409, 'ALREADY_VOTED', 'You have already voted in this poll')
    );
    vi.mocked(api.getResults).mockResolvedValue(mockResults);

    renderComponent();

    const radioAws = await screen.findByLabelText('AWS');
    fireEvent.click(radioAws);

    const voteBtn = screen.getByRole('button', { name: /submit vote/i });
    fireEvent.click(voteBtn);

    // Should display calm duplicate message and switch to results
    expect(await screen.findByText(/you have already voted in this poll/i)).toBeInTheDocument();
  });
});
