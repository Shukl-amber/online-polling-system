import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Plus, X, ArrowLeft } from 'lucide-react';
import { createPoll } from '../../shared/api';
import { ApiError } from '../../shared/types';
import { Button } from '../../shared/components/Button';
import { Input } from '../../shared/components/Input';
import { ErrorBanner } from '../../shared/components/index';
import styles from './CreatePoll.module.css';

function validateTitle(v: string): string | undefined {
  const t = v.trim();
  if (t.length < 3) return 'Title must be at least 3 characters';
  if (t.length > 120) return 'Title must be at most 120 characters';
  return undefined;
}

function validateQuestion(v: string): string | undefined {
  const t = v.trim();
  if (!t) return 'Question is required';
  if (t.length > 300) return 'Question must be at most 300 characters';
  return undefined;
}

function validateOptions(opts: string[]): string | undefined {
  const trimmed = opts.map((o) => o.trim());
  if (trimmed.filter((o) => o.length > 0).length < 2) {
    return 'At least 2 options are required';
  }
  const seen = new Set<string>();
  for (const opt of trimmed) {
    if (opt.length > 80) return `Option "${opt.slice(0, 20)}..." is too long (max 80)`;
    const lower = opt.toLowerCase();
    if (lower && seen.has(lower)) return `Duplicate option: ${opt}`;
    if (lower) seen.add(lower);
  }
  return undefined;
}

export function CreatePollPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState(['', '']);
  const [touched, setTouched] = useState(false);

  const mutation = useMutation({
    mutationFn: createPoll,
    onSuccess: (data) => {
      navigate(`/polls/${data.pollId}`);
    },
  });

  const titleError = touched ? validateTitle(title) : undefined;
  const questionError = touched ? validateQuestion(question) : undefined;
  const optionsError = touched ? validateOptions(options) : undefined;

  const isValid =
    !validateTitle(title) &&
    !validateQuestion(question) &&
    !validateOptions(options);

  function addOption() {
    if (options.length < 6) {
      setOptions([...options, '']);
    }
  }

  function removeOption(index: number) {
    if (options.length > 2) {
      setOptions(options.filter((_, i) => i !== index));
    }
  }

  function updateOption(index: number, value: string) {
    const next = [...options];
    next[index] = value;
    setOptions(next);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (!isValid) return;

    mutation.mutate({
      title: title.trim(),
      question: question.trim(),
      options: options.map((o) => o.trim()).filter((o) => o.length > 0),
    });
  }

  return (
    <div className={styles.createPage}>
      <h1 className={styles.pageTitle}>New poll</h1>

      <form onSubmit={handleSubmit} className={styles.form} noValidate>
        {mutation.isError && (
          <ErrorBanner
            message={
              mutation.error instanceof ApiError
                ? mutation.error.message
                : 'Failed to create poll'
            }
          />
        )}

        <div>
          <Input
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={() => setTouched(true)}
            error={titleError}
            placeholder="What is this poll about?"
            maxLength={120}
          />
          <p className={styles.charCount}>{title.trim().length} / 120</p>
        </div>

        <div>
          <Input
            label="Question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onBlur={() => setTouched(true)}
            error={questionError}
            placeholder="Ask your question"
            maxLength={300}
          />
          <p className={styles.charCount}>{question.trim().length} / 300</p>
        </div>

        <div className={styles.optionsSection}>
          <span className={styles.optionsLabel}>
            Options ({options.filter((o) => o.trim()).length} / 6)
          </span>
          {optionsError && touched && (
            <span role="alert" style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-danger)' }}>
              {optionsError}
            </span>
          )}
          {options.map((opt, i) => (
            <div key={i} className={styles.optionRow}>
              <div className={styles.optionInput}>
                <Input
                  label={`Option ${i + 1}`}
                  value={opt}
                  onChange={(e) => updateOption(i, e.target.value)}
                  placeholder={`Option ${i + 1}`}
                  maxLength={80}
                />
              </div>
              {options.length > 2 && (
                <button
                  type="button"
                  className={styles.removeButton}
                  onClick={() => removeOption(i)}
                  aria-label={`Remove option ${i + 1}`}
                >
                  <X size={18} strokeWidth={2} />
                </button>
              )}
            </div>
          ))}
          {options.length < 6 && (
            <Button
              type="button"
              variant="secondary"
              onClick={addOption}
              className={styles.addOptionButton}
            >
              <Plus size={18} strokeWidth={2} />
              Add option
            </Button>
          )}
        </div>

        <div className={styles.formActions}>
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate('/polls')}
          >
            <ArrowLeft size={18} strokeWidth={2} />
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={mutation.isPending || !isValid}
          >
            {mutation.isPending ? 'Creating...' : 'Create poll'}
          </Button>
        </div>
      </form>
    </div>
  );
}
