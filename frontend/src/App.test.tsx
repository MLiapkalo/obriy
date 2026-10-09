import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithQueryClient } from './test/render';
import App from './App';

describe('App', () => {
  it('renders the heading', () => {
    renderWithQueryClient(<App />);
    const headingElement = screen.getByRole('heading', { name: /Obriy/i });
    expect(headingElement).toBeInTheDocument();
  });
});
