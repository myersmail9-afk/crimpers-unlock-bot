"""One-shot catch-up run. This is what GitHub Actions executes on a schedule."""
from unlock_core import sweep

if __name__ == "__main__":
    unlocked = sweep()
    if unlocked:
        print(f"Unlocked {len(unlocked)}: {', '.join(unlocked)}")
    else:
        print("Nothing to unlock.")
