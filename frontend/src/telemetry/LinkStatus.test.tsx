import { describe, expect, it, beforeEach, afterAll } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LinkStatus } from './LinkStatus';
import { telemetryStore, type LinkStatus as LinkStatusType } from './store';

describe('LinkStatus', () => {
  beforeEach(() => {
    telemetryStore.setState(telemetryStore.getInitialState());
  });

  afterAll(() => {
    telemetryStore.setState(telemetryStore.getInitialState());
  });

  it.each<[LinkStatusType, string]>([
    ['connecting', 'Link: connecting'],
    ['live', 'Link: live'],
    ['stale', 'Link: stale'],
    ['lost', 'Link: lost'],
  ])('shows correct status for %s', async (status, expectedText) => {
    telemetryStore.setState({ status });
    render(<LinkStatus />);
    expect(await screen.findByText(expectedText)).toBeInTheDocument();
  });
});
