# SSH Deployer Automation

Automated SSH key deployment workflow for squad agents.

## Features

- **Status Checking**: Check which agents have SSH keys deployed
- **Automated Deployment**: Deploy keys to agents that need them
- **Verification**: Verify deployment success
- **Memory Integration**: Save status to memory for squad digest
- **Multiple Modes**: Interactive and automated modes

## Requirements

- Python 3.6+
- SSH key pair already generated (`~/.ssh/id_rsa.pub`)
- `ssh-key-deployer` tool installed in `~/workspace/tools/ssh-key-deployer`
- `squad-ssh-status` tool installed in `~/workspace/tools/squad-ssh-status`

## Installation

```bash
cd ~/workspace/tools/ssh-deployer-automation
chmod +x main.py
```

## Usage

### Check deployment status

```bash
python3 main.py check
```

### Deploy SSH keys (interactive)

```bash
python3 main.py deploy
```

### Deploy to specific agents

```bash
python3 main.py deploy Seneca Galen
```

### Verify deployment

```bash
python3 main.py verify
```

### Full automated workflow

```bash
python3 main.py auto
```

This runs:
1. Status check
2. Deployment (if needed)
3. Verification
4. Saves status to memory

## Squad Agents

- Seneca (lobster-1)
- Marcus (marcus-squad)
- Galen (galen-squad)
- Argus (argus-squad)

## Integration with Other Tools

This automation tool orchestrates:
- `ssh-key-deployer/main.py` - Does the actual deployment
- `squad-ssh-status/main.py` - Checks status

## Output

Status is automatically saved to `~/workspace/memory/YYYY-MM-DD.md` for inclusion in squad digests.

## Troubleshooting

### Deployment fails

Check that:
1. You have SSH keys generated (`~/.ssh/id_rsa.pub`)
2. Agents are reachable via network
3. You have password access to agents for initial deployment

### Status shows old information

The status tool checks live SSH connectivity. If showing old info, run:
```bash
python3 main.py check
```

## Example Output

```
[INFO] Checking SSH key deployment status...
Squad SSH Key Deployment Status
============================================================
⚠ Seneca     (lobster-1           ) - SSH key NOT deployed
✓ Marcus     (marcus-squad        ) - SSH key deployed
⚠ Galen      (galen-squad         ) - SSH key NOT deployed
⚠ Argus      (argus-squad         ) - SSH key NOT deployed
============================================================
Summary: 1/4 agents have SSH keys deployed

[INFO] Deploying SSH keys to: Seneca, Galen, Argus
...
[INFO] SSH keys deployed successfully!
[INFO] All agents have SSH keys: Seneca, Marcus, Galen, Argus
[INFO] Status saved to /home/exedev/.openclaw/workspace/memory/2026-05-22.md
```

## License

MIT