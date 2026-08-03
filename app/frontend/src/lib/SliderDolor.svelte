<script>
  /** Deslizador de dolor 0–10 con gradiente semáforo (spec §2). bind:valor */
  let { valor = $bindable(0) } = $props();
</script>

<div>
  <input
    bind:value={valor}
    type="range"
    min="0"
    max="10"
    step="1"
    aria-label="Dolor de 0 a 10"
    class="slider-dolor w-full"
  />
  <div class="mt-1 flex justify-between text-xs text-tenue">
    <span>0 · sin dolor</span>
    <span>10 · máximo</span>
  </div>
</div>

<style>
  .slider-dolor {
    -webkit-appearance: none;
    appearance: none;
    height: 26px;
    border-radius: 13px;
    background:
      linear-gradient(#10131a, #10131a) padding-box,
      linear-gradient(90deg, #3ecf6e 0%, #e0b34f 55%, #e05a4a 100%) border-box;
    border: 6px solid transparent;
    outline: none;
  }
  .slider-dolor::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #e8eaf0;
    border: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    cursor: pointer;
  }
  .slider-dolor::-moz-range-thumb {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #e8eaf0;
    border: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    cursor: pointer;
  }
</style>
