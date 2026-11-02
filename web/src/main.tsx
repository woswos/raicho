import { render } from 'preact';

import { App } from './app.js';

const root = document.getElementById('app');
if (!root) throw new Error('The page has no application root.');
render(<App />, root);
