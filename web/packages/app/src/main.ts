import { mount } from 'svelte';
import App from './App.svelte';
import UnsupportedBanner from './components/UnsupportedBanner.svelte';
import { webMidiSupported } from './midi/webMidiTransport.js';
import './app.css';

const target = document.getElementById('app')!;

const component = webMidiSupported()
  ? mount(App, { target })
  : mount(UnsupportedBanner, { target });

export default component;
