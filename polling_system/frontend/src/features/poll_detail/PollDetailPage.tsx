import { useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, User, Vote, RefreshCw, Lock, Info } from 'lucide-react';
import { getPoll, castVote, getResults, closePoll } from '../../shared/api';
import { ApiError, type PollResults } from '../../shared/types';
import { Button } from '../../shared/components/Button';
import {
  Badge,
  ErrorBanner,
  ConfirmDialog,
  Skeleton,
} from '../../shared/components/index';
import styles from './PollDetail.module.css';

export function PollDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [showCloseDialog, setShowCloseDialog] = useState(false);
  const [voteError, setVoteError] = useState<string | null>(null);
  const [duplicateMessage, setDuplicateMessage] = useState<string | null>(null);

  const pollQuery = useQuery({
    queryKey: ['poll', id],
    queryFn: () => getPoll(id!),
    enabled: !!id,
  });

  const resultsQuery = useQuery({
    queryKey: ['results', id],
    queryFn: () => getResults(id!),
    enabled: !!id && (showResults || Boolean(pollQuery.data?.hasVoted) || pollQuery.data?.status === 'closed'),
  });

  const voteMutation = useMutation({
    mutationFn: (optionId: string) => castVote(id!, { optionId }),
    onSuccess: () => {
      setShowResults(true);
      setVoteError(null);
      setDuplicateMessage(null);
      queryClient.invalidateQueries({ queryKey: ['poll', id] });
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError && error.code === 'ALREADY_VOTED') {
        setDuplicateMessage(error.message);
        setShowResults(true);
        setVoteError(null);
      } else {
        setVoteError(error instanceof ApiError ? error.message : 'Failed to cast vote');
      }
    },
  });

  const closeMutation = useMutation({
    mutationFn: () => closePoll(id!),
    onSuccess: () => {
      setShowCloseDialog(false);
      queryClient.invalidateQueries({ queryKey: ['poll', id] });
    },
  });

  const handleVote = useCallback(() => {
    if (selectedOption) {
      voteMutation.mutate(selectedOption);
    }
  }, [selectedOption, voteMutation]);

  const handleRefreshResults = useCallback(() => {
    resultsQuery.refetch();
  }, [resultsQuery]);

  const poll = pollQuery.data;
  const results: PollResults | undefined = resultsQuery.data;
  const hasVoted = poll?.hasVoted || voteMutation.isSuccess;
  const isClosed = poll?.status === 'closed';
  const showVoting = !hasVoted && !isClosed && !showResults;

  // Show results automatically if user has voted or poll is closed
  const shouldShowResults = hasVoted || isClosed || showResults;

  if (!shouldShowResults && poll?.hasVoted) {
    setShowResults(true);
  }

  return (
    <div className={styles.detailPage}>
      <Link to="/polls" className={styles.backLink}>
        <ArrowLeft size={16} strokeWidth={2} />
        All polls
      </Link>

      {pollQuery.isLoading && (
        <>
          <Skeleton width="70%" height="2rem" />
          <div style={{ height: '1rem' }} />
          <Skeleton width="50%" height="1.125rem" />
        </>
      )}

      {pollQuery.isError && (
        <ErrorBanner
          message={
            pollQuery.error instanceof ApiError
              ? pollQuery.error.message
              : 'Failed to load poll'
          }
          action={
            <Button variant="secondary" onClick={() => pollQuery.refetch()}>
              Retry
            </Button>
          }
        />
      )}

      {poll && (
        <>
          <div className={styles.pollHeader}>
            <h1 className={styles.pollTitle}>{poll.title}</h1>
            <p className={styles.pollQuestion}>{poll.question}</p>
            <div className={styles.pollMeta}>
              <span className={styles.metaItem}>
                <User size={14} strokeWidth={2} />
                {poll.createdByName}
              </span>
              <span className={styles.metaItem}>
                <Vote size={14} strokeWidth={2} />
                {poll.totalVotes} vote{poll.totalVotes !== 1 ? 's' : ''}
              </span>
              <Badge status={poll.status} />
            </div>
          </div>

          {duplicateMessage && (
            <div className={styles.duplicateMessage}>
              <Info size={18} strokeWidth={2} />
              {duplicateMessage}
            </div>
          )}

          {voteError && <ErrorBanner message={voteError} />}

          {showVoting && (
            <div className={styles.voteCard}>
              <h2 className={styles.voteTitle}>Cast your vote</h2>
              <div className={styles.radioGroup} role="radiogroup" aria-label="Poll options">
                {poll.options.map((opt) => (
                  <label
                    key={opt.id}
                    className={`${styles.radioLabel} ${selectedOption === opt.id ? styles.selected : ''}`}
                  >
                    <input
                      type="radio"
                      name="vote"
                      value={opt.id}
                      checked={selectedOption === opt.id}
                      onChange={() => setSelectedOption(opt.id)}
                      className={styles.radioInput}
                    />
                    {opt.text}
                  </label>
                ))}
              </div>
              <div className={styles.voteActions}>
                <Button
                  onClick={handleVote}
                  disabled={!selectedOption || voteMutation.isPending}
                >
                  {voteMutation.isPending ? 'Voting...' : 'Submit vote'}
                </Button>
              </div>
            </div>
          )}

          {shouldShowResults && (
            <div className={styles.resultsCard}>
              <div className={styles.resultsHeader}>
                <h2 className={styles.resultsTitle}>Results</h2>
                <div className={styles.resultsMeta}>
                  {resultsQuery.dataUpdatedAt > 0 && (
                    <span>
                      Updated {new Date(resultsQuery.dataUpdatedAt).toLocaleTimeString()}
                    </span>
                  )}
                  <Button
                    variant="ghost"
                    onClick={handleRefreshResults}
                    disabled={resultsQuery.isFetching}
                    aria-label="Refresh results"
                  >
                    <RefreshCw
                      size={16}
                      strokeWidth={2}
                      style={{
                        animation: resultsQuery.isFetching ? 'spin 1s linear infinite' : 'none',
                      }}
                    />
                    Refresh
                  </Button>
                </div>
              </div>

              {resultsQuery.isLoading && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {Array.from({ length: poll.options.length }).map((_, i) => (
                    <div key={i}>
                      <Skeleton width="40%" height="0.875rem" />
                      <div style={{ height: '0.5rem' }} />
                      <Skeleton width="100%" height="8px" />
                    </div>
                  ))}
                </div>
              )}

              {results && (
                <>
                  <div className={styles.resultsList}>
                    {results.options.map((opt) => (
                      <div key={opt.id} className={styles.resultItem}>
                        <div className={styles.resultLabel}>
                          <span className={styles.resultText}>
                            {opt.text}
                            {opt.id === results.userChoice && ' (your vote)'}
                          </span>
                          <span className={styles.resultNumbers}>
                            {opt.count} ({opt.percentage}%)
                          </span>
                        </div>
                        <div className={styles.resultBarTrack}>
                          <div
                            className={`${styles.resultBarFill} ${opt.id === results.userChoice ? styles.userChoice : ''}`}
                            style={{ width: `${opt.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className={styles.totalVotes}>
                    Total: {results.totalVotes} vote{results.totalVotes !== 1 ? 's' : ''}
                  </p>
                </>
              )}

              {resultsQuery.isError && (
                <ErrorBanner
                  message="Failed to load results"
                  action={
                    <Button variant="secondary" onClick={handleRefreshResults}>
                      Retry
                    </Button>
                  }
                />
              )}
            </div>
          )}

          {!isClosed && poll.createdBy && (
            <div className={styles.closeSection}>
              <Button
                variant="danger"
                onClick={() => setShowCloseDialog(true)}
              >
                <Lock size={16} strokeWidth={2} />
                Close poll
              </Button>
            </div>
          )}

          <ConfirmDialog
            open={showCloseDialog}
            title="Close this poll?"
            body="Once closed, no more votes can be cast. Results will remain visible. This action cannot be undone."
            confirmLabel="Close poll"
            onConfirm={() => closeMutation.mutate()}
            onCancel={() => setShowCloseDialog(false)}
            loading={closeMutation.isPending}
          />
        </>
      )}
    </div>
  );
}
