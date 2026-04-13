class SelectionStore {
  bank = $state(0);
  encoder = $state(0);
  multiSelection = $state<Set<number>>(new Set());

  select(bank: number, encoder: number): void {
    this.bank = bank;
    this.encoder = encoder;
  }

  setBank(bank: number): void {
    this.bank = bank;
    // Reset multi-selection when switching banks so it doesn't leak across banks.
    this.multiSelection = new Set();
  }

  editTargets(): number[] {
    if (this.multiSelection.size > 0) {
      return [...this.multiSelection].sort((a, b) => a - b);
    }
    return [this.encoder];
  }
}

export const selectionStore = new SelectionStore();
