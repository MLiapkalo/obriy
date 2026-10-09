import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Testing Library only auto-unmounts when test globals are enabled; we import them explicitly instead.
afterEach(cleanup);
