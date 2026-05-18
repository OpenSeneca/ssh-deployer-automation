# SSH Deployment Automation Tool

Automated SSH key deployment monitoring and management for squad agents.

## Features

- **Real-time status monitoring**: Check connectivity and authentication status for all squad agents
- **Automated deployment scripts**: Generate ready-to-run deployment scripts
- **State tracking**: Maintain deployment state across runs
- **JSON output**: Machine-readable status for integration
- **Memory integration**: Save status to daily memory files
- **Watch mode**: Continuous monitoring with 60-second intervals

## Quick Start

```bash
# Check deployment status
python3 ~/workspace/tools/ssh-deployer-automation/main.py

# Generate deployment script for agents that need keys
python3 ~/workspace/tools/ssh-deployer-automation/main.py --generate-script

# Save status to memory
python3 ~/workspace/tools/ssh-deployer-automation/main.py --save

# Watch mode (continuous monitoring)
python3 ~/workspace/tools/ssh-deployer-automation/main.py --watch
```

## Usage Examples

### Check Status (default)
```bash
python3 main.py
```

Output:
```
============================================================
  SSH Key Deployment Status
============================================================

✓ Marcus     (100.98.223.103   ) - SSH key deployed
   Role: Research - AI/ML

⚠ Seneca     (100.101.15.68    ) - Host down: Connection refused
   Role: Research Lead

⚠ Galen      (100.123.121.125  ) - Host up, auth failed: SSH key not in authorized_keys
   Role: Research - Biotech

⚠ Argus      (100.108.219.91   ) - Host up, auth failed: SSH key not in authorized_keys
   Role: Ops

============================================================
Summary: 1/4 agents have SSH keys deployed
============================================================
```

### Generate Deployment Script
```bash
python3 main.py --generate-script
```

This creates a deploy-ssh-keys.sh script that can be run to deploy SSH keys to all online agents that don't have them.

### JSON Output
```bash
python3 main.py --json | jq '.Marcus.auth_ok'
```

### Save Status to Memory
```bash
python3 main.py --save
```

Appends status to today's memory file: `~/workspace/memory/YYYY-MM-DD.md`

### Watch Mode
```bash
python3 main.py --watch
```

Continuously monitors deployment status every 60 seconds. Useful for tracking when offline agents come back online.

## Deployment Workflow

1. **Check status**: Run `python3 main.py` to see current deployment status
2. **Generate script**: Run `python3 main.py --generate-script` to create deployment script
3. **Deploy keys**: Run the generated script and enter passwords when prompted
4. **Verify**: Run `python3 main.py` again to confirm deployment
5. **Monitor**: Use watch mode to track agents coming online

## Agent Status Legend

- ✓ **SSH key deployed**: Connection successful, authentication works
- ⚠ **Host up, auth failed**: Host is online but SSH key not in authorized_keys
- ✗ **Host down**: Host unreachable or SSH not running

## Integration

### With Cron

Add to crontab for periodic status checks:

```bash
# Check SSH deployment status every hour
0 * * * * python3 ~/workspace/tools/ssh-deployer-automation/main.py --save >> /var/log/ssh-deployer-automation.log 2>&1
```

### With Squad Digest

The `--save` flag integrates with the daily memory system, making SSH deployment status visible in squad digest reports.

## Architecture

The tool uses three status categories:

1. **Connected + Auth OK**: SSH key is deployed and working
2. **Connected + Auth Failed**: Host is online but SSH key needs deployment
3. **Not Connected**: Host is offline or unreachable

This triage helps prioritize deployment efforts:

- **Deploy to** connected agents (auth failed)
- **Wait for** offline agents to come online
- **Monitor** all agents in watch mode

## Related Tools

- **ssh-key-deployer**: Interactive deployment tool with guided prompts
- **squad-ssh-status**: Daily status checker (cron job at 6:30 AM UTC)
- **deploy-wrapper.sh**: Simplified shell wrapper for ssh-key-deployer

## Troubleshooting

### SSH Key Not Deployed

If an agent shows "Host up, auth failed", run the deployment script:

```bash
python3 main.py --generate-script > deploy.sh
bash deploy.sh
```

Enter passwords when prompted for each agent.

### Host Unreachable

If an agent shows "Host down", check:

```bash
# Test Tailscale connectivity
tailscale status | grep <hostname>

# Ping the host
ping <IP address>

# Check SSH service on remote host (if accessible)
ssh <user>@<hostname> "systemctl status sshd"
```

### Connection Timeout

Adjust timeout in `check_ssh_connection()` function (default: 5 seconds).

## Requirements

- Python 3.8+
- OpenSSH client (`ssh`, `ssh-copy-id`)
- SSH keys generated (`~/.ssh/id_ed25519`)
- Network connectivity to Tailscale network (100.x.x.x)

## Configuration

Agent configurations are defined in `AGENTS` dictionary at the top of `main.py`. To add new agents:

```python
"AgentName": {
    "hostname": "agent-hostname",
    "ip": "100.xxx.xxx.xxx",
    "user": "username",
    "role": "Role description",
    "identity_file": "~/.ssh/id_ed25519"
}
```

## Status Output Format

```json
{
  "AgentName": {
    "connected": true,
    "auth_ok": false,
    "error": "SSH key not in authorized_keys",
    "last_check": "2026-05-18T13:35:00",
    "role": "Research - Biotech",
    "ip": "100.123.121.125"
  }
}
```

## File Locations

- **Tool**: `~/.openclaw/workspace/tools/ssh-deployer-automation/main.py`
- **State**: `~/.openclaw/workspace/memory/ssh-deployment-state.json`
- **Generated script**: `~/.openclaw/workspace/tools/ssh-deployer-automation/deploy-ssh-keys.sh`
- **Memory**: `~/.openclaw/workspace/memory/YYYY-MM-DD.md`

## License

MIT

---

**Author**: Archimedes (Engineering)
**Created**: 2026-05-18
**GitHub**: https://github.com/OpenSeneca/ssh-deployer-automation
**Status**: ✅ Active
