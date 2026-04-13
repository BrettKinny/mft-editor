<script lang="ts">
  import DeviceConnectBar from './components/DeviceConnectBar.svelte';
  import DeviceView from './components/DeviceView.svelte';
  import EncoderSettings from './components/EncoderSettings.svelte';
  import GlobalSettings from './components/GlobalSettings.svelte';
  import MultiEdit from './components/MultiEdit.svelte';
</script>

<DeviceConnectBar />

<main>
  <div class="left">
    <DeviceView />
    <MultiEdit />
    <GlobalSettings />
  </div>
  <div class="right">
    <EncoderSettings />
  </div>
</main>

<style>
  main {
    flex: 1;
    display: grid;
    grid-template-columns: minmax(360px, 1fr) minmax(480px, 1.3fr);
    gap: 14px;
    padding: 14px;
    min-height: 0;
  }

  .left,
  .right {
    display: flex;
    flex-direction: column;
    gap: 14px;
    min-width: 0;
  }

  @media (max-width: 1000px) {
    main {
      grid-template-columns: 1fr;
    }
  }
</style>
