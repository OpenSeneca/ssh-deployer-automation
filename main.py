#!/usr/bin/env python3
"""
SSH Deployment Automation Tool
Monitors and automates SSH key deployment for squad agents.
Checks connectivity, authentication status, and generates deployment scripts.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Squad agents configuration
AGENTS = {
    "Seneca": {
        "hostname": "lobster-1",
        "ip": "100.101.15.68",
        "user": "exedev",
        "role": "Research Lead",
        "identity_file": "~/.ssh/id_ed25519"
    },
    "Marcus": {
        "hostname": "marcus-squad",
        "ip": "100.98.223.103",
        "user": "exedev",
        "role": "Research - AI/ML",
        "identity_file": "~/.ssh/id_ed25519"
    },
    "Galen": {
        "hostname": "galen-squad",
        "ip": "100.123.121.125",
        "user": "exedev",
        "role": "Research - Biotech",
        "identity_file": "~/.ssh/id_ed25519"
    },
    "Argus": {
        "hostname": "argus-squad",
        "ip": "100.108.219.91",
        "user": "exedev",
        "role": "Ops",
        "identity_file": "~/.ssh/id_ed25519"
    }
}

# State file for tracking deployment progress
STATE_FILE = Path.home() / ".openclaw" / "workspace" / "memory" / "ssh-deployment-state.json"

def load_state():
    """Load deployment state from JSON file"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """Save deployment state to JSON file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_ssh_connection(hostname, user, identity_file):
    """Check if SSH connection works (no password required)"""
    try:
        cmd = [
            "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
            f"{user}@{hostname}", "echo 'OK'"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "OK" in result.stdout:
            return True, result.stderr
        return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Connection timeout"
    except Exception as e:
        return False, str(e)

def get_deployment_status():
    """Get current deployment status for all agents"""
    status = {}
    state = load_state()
    
    for agent_name, config in AGENTS.items():
        hostname = config["hostname"]
        user = config["user"]
        identity_file = config["identity_file"]
        
        # Check SSH connection
        connected, error = check_ssh_connection(hostname, user, identity_file)
        
        # Determine status
        if connected:
            status[agent_name] = {
                "connected": True,
                "auth_ok": True,
                "error": None,
                "last_check": datetime.now().isoformat(),
                "role": config["role"],
                "ip": config["ip"]
            }
        else:
            # Parse error to determine if host is down or auth failed
            if "Connection refused" in error or "timed out" in error or "timeout" in error.lower():
                status[agent_name] = {
                    "connected": False,
                    "auth_ok": False,
                    "error": "Host unreachable or SSH not running",
                    "last_check": datetime.now().isoformat(),
                    "role": config["role"],
                    "ip": config["ip"]
                }
            elif "Permission denied" in error:
                status[agent_name] = {
                    "connected": True,
                    "auth_ok": False,
                    "error": "SSH key not in authorized_keys",
                    "last_check": datetime.now().isoformat(),
                    "role": config["role"],
                    "ip": config["ip"]
                }
            else:
                status[agent_name] = {
                    "connected": False,
                    "auth_ok": False,
                    "error": error,
                    "last_check": datetime.now().isoformat(),
                    "role": config["role"],
                    "ip": config["ip"]
                }
    
    return status

def print_status(status, json_output=False):
    """Print deployment status"""
    if json_output:
        print(json.dumps(status, indent=2))
        return
    
    print("\n" + "=" * 60)
    print("  SSH Key Deployment Status")
    print("=" * 60)
    print()
    
    deployed_count = 0
    total_count = len(status)
    
    for agent_name, info in sorted(status.items()):
        if info["auth_ok"]:
            symbol = "✓"
            status_text = "SSH key deployed"
            deployed_count += 1
        elif info["connected"]:
            symbol = "⚠"
            status_text = f"Host up, auth failed: {info['error']}"
        else:
            symbol = "✗"
            status_text = f"Host down: {info['error']}"
        
        hostname = info.get("ip", "?")
        print(f"{symbol} {agent_name:10} ({hostname:15}) - {status_text}")
        print(f"   Role: {info['role']}")
        print()
    
    print("=" * 60)
    print(f"Summary: {deployed_count}/{total_count} agents have SSH keys deployed")
    print("=" * 60)
    print()

def generate_deployment_script(status):
    """Generate a deployment script for agents that need keys"""
    script_lines = [
        "#!/bin/bash",
        "# SSH Key Deployment Script",
        "# Generated by ssh-deployer-automation",
        f"# Generated: {datetime.now().isoformat()}",
        "",
        "set -e",
        "",
        "echo 'Starting SSH key deployment...'",
        "echo ''",
    ]
    
    needs_deployment = []
    for agent_name, info in status.items():
        if info["connected"] and not info["auth_ok"]:
            hostname = AGENTS[agent_name]["hostname"]
            user = AGENTS[agent_name]["user"]
            needs_deployment.append((agent_name, hostname, user))
    
    if not needs_deployment:
        script_lines.append("echo 'All agents already have SSH keys deployed!'")
    else:
        for agent_name, hostname, user in needs_deployment:
            script_lines.append(f"echo 'Deploying SSH key to {agent_name} ({user}@{hostname})...'")
            script_lines.append(f"ssh-copy-id -i ~/.ssh/id_ed25519.pub {user}@{hostname}")
            script_lines.append("")
        
        script_lines.append("echo ''")
        script_lines.append("echo 'Deployment complete!'")
        script_lines.append("echo 'Verify deployment with: python3 ~/workspace/tools/ssh-deployer-automation/main.py'")
    
    return "\n".join(script_lines)

def save_status_to_memory(status):
    """Append status to today's memory file"""
    memory_dir = Path.home() / ".openclaw" / "workspace" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = memory_dir / f"{today}.md"
    
    # Count deployed agents
    deployed = sum(1 for info in status.values() if info["auth_ok"])
    total = len(status)
    
    entry = f"\n## SSH Deployment Status ({datetime.now().strftime('%H:%M UTC')})\n"
    entry += f"- Deployed: {deployed}/{total} agents\n"
    
    for agent_name, info in sorted(status.items()):
        if info["auth_ok"]:
            entry += f"  - ✓ {agent_name}: SSH key deployed\n"
        else:
            entry += f"  - ✗ {agent_name}: {info['error']}\n"
    
    with open(memory_file, 'a') as f:
        f.write(entry)
    
    print(f"Status saved to {memory_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SSH Deployment Automation Tool")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--generate-script", action="store_true", help="Generate deployment script")
    parser.add_argument("--save", action="store_true", help="Save status to memory")
    parser.add_argument("--watch", action="store_true", help="Watch mode (continuous monitoring)")
    args = parser.parse_args()
    
    status = get_deployment_status()
    
    if args.json:
        print_status(status, json_output=True)
    elif args.generate_script:
        script = generate_deployment_script(status)
        print(script)
        # Save to file
        script_file = Path.home() / ".openclaw" / "workspace" / "tools" / "ssh-deployer-automation" / "deploy-ssh-keys.sh"
        with open(script_file, 'w') as f:
            f.write(script)
        script_file.chmod(0o755)
        print(f"\nScript saved to {script_file}")
    elif args.save:
        save_status_to_memory(status)
    elif args.watch:
        print("Watch mode enabled. Press Ctrl+C to stop...")
        print()
        try:
            while True:
                status = get_deployment_status()
                print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print_status(status, json_output=False)
                import time
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nWatch mode stopped.")
    else:
        print_status(status)
        
        # Show next steps
        connected_no_auth = [name for name, info in status.items() 
                            if info["connected"] and not info["auth_ok"]]
        
        if connected_no_auth:
            print("To deploy SSH keys to online agents:")
            print(f"  python3 {sys.argv[0]} --generate-script > deploy.sh")
            print("  bash deploy.sh")
            print()

if __name__ == "__main__":
    main()
