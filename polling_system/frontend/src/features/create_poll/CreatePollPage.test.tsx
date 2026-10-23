import '@testing-library/jest-dom/vitest';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CreatePollPage } from './CreatePollPage';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
}

describe('CreatePollPage', () => {
  it('renders initial form fields with disabled submit button', () => {
    renderWithProviders(<CreatePollPage />);

    expect(screen.getByLabelText(/^title$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^question$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create poll/i })).toBeDisabled();
  });

  it('allows adding and removing option rows within 2-6 range', () => {
    renderWithProviders(<CreatePollPage />);

    // Initially 2 options
    expect(screen.getByPlaceholderText('Option 1')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Option 2')).toBeInTheDocument();

    // Add option button is available
    const addBtn = screen.getByRole('button', { name: /add option/i });
    fireEvent.click(addBtn);
    expect(screen.getByPlaceholderText('Option 3')).toBeInTheDocument();

    // Remove option 3 using its specific accessible label
    const removeBtn3 = screen.getByLabelText('Remove option 3');
    fireEvent.click(removeBtn3);
    expect(screen.queryByPlaceholderText('Option 3')).not.toBeInTheDocument();
  });

  it('validates duplicate options and keeps submit button disabled', () => {
    renderWithProviders(<CreatePollPage />);

    const titleInput = screen.getByLabelText(/^title$/i);
    const questionInput = screen.getByLabelText(/^question$/i);
    const opt1 = screen.getByPlaceholderText('Option 1');
    const opt2 = screen.getByPlaceholderText('Option 2');

    fireEvent.change(titleInput, { target: { value: 'Valid Title' } });
    fireEvent.change(questionInput, { target: { value: 'Valid question text?' } });
    fireEvent.blur(titleInput);
    fireEvent.change(opt1, { target: { value: 'Option A' } });
    fireEvent.change(opt2, { target: { value: 'option a' } }); // duplicate case-insensitive

    const submitBtn = screen.getByRole('button', { name: /create poll/i });
    expect(submitBtn).toBeDisabled();
    expect(screen.getByText(/duplicate option/i)).toBeInTheDocument();
  });

  it('enables submit button when all fields are valid', () => {
    renderWithProviders(<CreatePollPage />);

    const titleInput = screen.getByLabelText(/^title$/i);
    const questionInput = screen.getByLabelText(/^question$/i);
    const opt1 = screen.getByPlaceholderText('Option 1');
    const opt2 = screen.getByPlaceholderText('Option 2');

    fireEvent.change(titleInput, { target: { value: 'Valid Title' } });
    fireEvent.change(questionInput, { target: { value: 'What is your favorite cloud provider?' } });
    fireEvent.change(opt1, { target: { value: 'AWS' } });
    fireEvent.change(opt2, { target: { value: 'GCP' } });

    const submitBtn = screen.getByRole('button', { name: /create poll/i });
    expect(submitBtn).not.toBeDisabled();
  });
});
