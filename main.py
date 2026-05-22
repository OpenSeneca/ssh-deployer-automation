#!/usr/bin/env python3
"""
SSH Deployer Automation
Automates the full SSH key deployment workflow for squad agents.

Features:
- Checks current deployment status
- Deploys keys to agents that need them
- Verifies deployment success
- Saves status to memory for squad digest
- Supports both interactive and automated modes
"""

import subprocess
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Paths
WORKSPACE = Path.home() / ".openclaw" / "workspace"
SSH_DEPLOYER = WORKSPACE / "tools" / "ssh-key-deployer"
SSH_STATUS = WORKSPACE / "tools" / "squad-ssh-status"
MEMORY_DIR = WORKSPACE / "memory"

# Agent list (squad members)
AGENTS = ["Seneca", "Galen", "Argus", "Marcus"]

class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def log_info(msg):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")

def log_warn(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def log_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def log_step(msg):
    print(f"{Colors.BLUE}[STEP]{Colors.NC} {msg}")

def check_status():
    """Check current SSH key deployment status."""
    log_step("Checking SSH key deployment status...")

    status_file = SSH_STATUS / "main.py"
    if not status_file.exists():
        log_error(f"Status tool not found: {status_file}")
        return None

    try:
        result = subprocess.run(
            ["python3", str(status_file), "--check"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)

        # Parse status
        deployed = []
        not_deployed = []

        for agent in AGENTS:
            if agent.lower() in result.stdout.lower() and "not deployed" in result.stdout.lower():
                not_deployed.append(agent)
            elif agent.lower() in result.stdout.lower() and "deployed" in result.stdout.lower():
                deployed.append(agent)

        return {
            "deployed": deployed,
            "not_deployed": not_deployed,
            "raw_output": result.stdout
        }
    except subprocess.TimeoutExpired:
        log_error("Status check timed out")
        return None
    except Exception as e:
        log_error(f"Error checking status: {e}")
        return None

def deploy_keys(agents=None, auto=False):
    """Deploy SSH keys to specified agents or all that need them."""
    status = check_status()
    if not status:
        return False

    to_deploy = agents or status["not_deployed"]

    if not to_deploy:
        log_info("All agents have SSH keys deployed. Nothing to do.")
        return True

    log_step(f"Deploying SSH keys to: {', '.join(to_deploy)}")

    deployer_file = SSH_DEPLOYER / "main.py"
    if not deployer_file.exists():
        log_error(f"Deployer tool not found: {deployer_file}")
        return False

    try:
        cmd = ["python3", str(deployer_file), "--deploy"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        print(result.stdout)

        if result.returncode != 0:
            log_error(f"Deployment failed: {result.stderr}")
            return False

        log_info("SSH keys deployed successfully!")
        return True

    except subprocess.TimeoutExpired:
        log_error("Deployment timed out")
        return False
    except Exception as e:
        log_error(f"Error deploying keys: {e}")
        return False

def verify_deployment():
    """Verify that SSH keys were deployed successfully."""
    log_step("Verifying SSH key deployment...")

    status = check_status()
    if not status:
        return False

    remaining = status["not_deployed"]
    deployed = status["deployed"]

    if remaining:
        log_warn(f"Still missing keys for: {', '.join(remaining)}")
        return False
    else:
        log_info(f"All agents have SSH keys: {', '.join(deployed)}")
        return True

def save_to_memory(status):
    """Save deployment status to memory for squad digest."""
    log_step("Saving status to memory...")

    if not MEMORY_DIR.exists():
        MEMORY_DIR.mkdir(parents=True)

    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = MEMORY_DIR / f"{today}.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    entry = f"""## SSH Deployment Status ({timestamp})

### Deployment Status
- Deployed: {', '.join(status.get('deployed', []))}
- Not Deployed: {', '.join(status.get('not_deployed', []))}
- Total: {len(status.get('deployed', []))}/{len(AGENTS)} agents

### Details
```
{status.get('raw_output', 'N/A')}
```

"""

    with open(memory_file, "a") as f:
        f.write(entry)

    log_info(f"Status saved to {memory_file}")

def full_workflow(auto=False):
    """Run the complete deployment workflow."""
    log_step("Starting SSH deployment workflow...")
    print()

    # Check status
    status = check_status()
    if not status:
        log_error("Cannot proceed without status information")
        return False

    print()

    # Deploy if needed
    if status["not_deployed"]:
        success = deploy_keys(auto=auto)
        if not success:
            log_error("Deployment failed")
            return False
    else:
        log_info("All agents already have SSH keys")

    print()

    # Wait for propagation
    log_info("Waiting for SSH key propagation...")
    import time
    time.sleep(3)

    print()

    # Verify
    status_after = check_status()
    if not status_after:
        log_error("Could not verify deployment")
        return False

    success = verify_deployment()
    print()

    # Save to memory
    save_to_memory(status_after)
    print()

    if success:
        log_info("✅ SSH deployment workflow completed successfully!")
    else:
        log_warn("⚠️  Deployment completed with issues")

    return success

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automate SSH key deployment for squad agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check              # Check deployment status
  %(prog)s deploy             # Deploy to agents needing keys
  %(prog)s verify             # Verify deployment
  %(prog)s auto               # Full automated workflow
  %(prog)s deploy Seneca Galen  # Deploy to specific agents
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check deployment status")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy SSH keys")
    deploy_parser.add_argument(
        "agents",
        nargs="*",
        help="Agents to deploy to (default: all needing keys)"
    )
    deploy_parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-deploy without prompts"
    )

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify deployment")

    # Auto command
    auto_parser = subparsers.add_parser("auto", help="Full automated workflow")

    args = parser.parse_args()

    if args.command == "check":
        check_status()
    elif args.command == "deploy":
        deploy_keys(args.agents, auto=args.auto)
    elif args.command == "verify":
        verify_deployment()
    elif args.command == "auto":
        success = full_workflow(auto=True)
        sys.exit(0 if success else 1)
    else:
        # Default: run full workflow in interactive mode
        full_workflow(auto=False)

if __name__ == "__main__":
    main()