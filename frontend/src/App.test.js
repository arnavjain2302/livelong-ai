import { render, screen } from '@testing-library/react';
import App from './App';

test('renders upload prescription navigation item', () => {
  render(<App />);
  expect(screen.getByRole('button', { name: /upload prescription/i })).toBeInTheDocument();
});
