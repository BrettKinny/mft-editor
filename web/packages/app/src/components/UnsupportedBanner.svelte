<script lang="ts"></script>

<div class="banner">
  <div class="card">
    <h1>Web MIDI not supported</h1>
    <p>
      The MFT Editor web app uses the <strong>Web MIDI API</strong>, which is
      only available in Chromium-based browsers.
    </p>
    <p>Please open this page in one of:</p>
    <ul>
      <li>Google Chrome</li>
      <li>Microsoft Edge</li>
      <li>Brave</li>
      <li>Arc</li>
      <li>Opera</li>
    </ul>
    <p class="dim">
      Firefox and Safari do not implement the Web MIDI API. If you prefer those
      browsers, use the PySide6 desktop editor from the same repo instead.
    </p>
  </div>
</div>

<style>
  .banner {
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 2rem;
  }

  .card {
    max-width: 520px;
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 2rem 2.25rem;
  }

  h1 {
    margin-bottom: 1rem;
    color: var(--warning);
  }

  p {
    margin: 0.75rem 0;
    color: var(--fg);
  }

  ul {
    color: var(--fg);
    padding-left: 1.25rem;
  }

  li {
    margin: 0.25rem 0;
  }

  .dim {
    color: var(--fg-dim);
    font-size: 12px;
    margin-top: 1.25rem;
    border-top: 1px solid var(--border);
    padding-top: 1rem;
  }
</style>
