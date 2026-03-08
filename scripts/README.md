# Scripts

Helper scripts for the repo. Run from the **project root** (or the script will change to it).

## commit-and-push

Add all changes, commit with a message, push to `origin main`.

**PowerShell (Windows):**
```powershell
.\scripts\commit-and-push.ps1 "Your commit message"
```

**Bash (WSL / Linux / Mac):**
```bash
chmod +x scripts/commit-and-push.sh   # once
./scripts/commit-and-push.sh "Your commit message"
```

If there’s nothing to commit, the script exits without error.
