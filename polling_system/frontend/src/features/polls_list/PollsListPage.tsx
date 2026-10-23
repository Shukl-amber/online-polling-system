import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { BarChart3, Plus, User, Vote } from 'lucide-react';
import { listPolls } from '../../shared/api';
import { Button } from '../../shared/components/Button';
import { Badge, EmptyState, ErrorBanner, Skeleton } from '../../shared/components/index';
import styles from './PollsList.module.css';

export function PollsListPage() {
  const navigate = useNavigate();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['polls'],
    queryFn: listPolls,
  });

  return (
    <div className={styles.listPage}>
      <div className={styles.header}>
        <h1 className={styles.pageTitle}>Polls</h1>
        <Button onClick={() => navigate('/polls/new')}>
          <Plus size={18} strokeWidth={2} />
          New poll
        </Button>
      </div>

      {isLoading && (
        <div className={styles.pollsList}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className={styles.skeletonCard}>
              <Skeleton width="60%" height="1.25rem" />
              <Skeleton width="40%" height="0.875rem" />
            </div>
          ))}
        </div>
      )}

      {isError && (
        <ErrorBanner
          message={error instanceof Error ? error.message : 'Failed to load polls'}
          action={
            <Button variant="secondary" onClick={() => refetch()}>
              Retry
            </Button>
          }
        />
      )}

      {data && data.polls.length === 0 && (
        <EmptyState
          icon={<BarChart3 size={48} strokeWidth={1.5} />}
          title="No polls yet"
          description="Create the first poll and share it with your class."
          action={
            <Button onClick={() => navigate('/polls/new')}>
              <Plus size={18} strokeWidth={2} />
              Create a poll
            </Button>
          }
        />
      )}

      {data && data.polls.length > 0 && (
        <div className={styles.pollsList}>
          {data.polls.map((poll) => (
            <Link
              to={`/polls/${poll.pollId}`}
              key={poll.pollId}
              className={styles.pollCard}
            >
              <div className={styles.pollInfo}>
                <span className={styles.pollTitle}>{poll.title}</span>
                <div className={styles.pollMeta}>
                  <span className={styles.pollMetaItem}>
                    <User size={14} strokeWidth={2} />
                    {poll.createdByName}
                  </span>
                  <span className={styles.pollMetaItem}>
                    <Vote size={14} strokeWidth={2} />
                    {poll.totalVotes} vote{poll.totalVotes !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>
              <div className={styles.pollRight}>
                <Badge status={poll.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
