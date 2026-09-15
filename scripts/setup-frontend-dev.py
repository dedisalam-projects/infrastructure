import sys
import subprocess
import os
import urllib.request
import time
import socket
from pathlib import Path

# Ensure UTF-8 streams on Windows to prevent UnicodeEncodeError
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_command(command, capture_output=False, env=None):
    """Executes a shell command deterministically and safely."""
    print(f"Executing: {' '.join(command)}")
    result = subprocess.run(command, capture_output=capture_output, text=True, env=env)
    if result.returncode != 0:
        if capture_output:
            print(f"Error output: {result.stderr}", file=sys.stderr)
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")
    return result.stdout.strip() if capture_output else None

def pull_images():
    """Step 1: Pull immutable production images"""
    print("\n[1/5] Pulling latest production images...")
    images = [
        "dedisalam/backend-gateway:latest",
        "dedisalam/backend-user-service:latest",
        "dedisalam/backend-notification-service:latest"
    ]
    for img in images:
        run_command(["docker", "pull", img])

def recreate_dev_stack():
    """Step 2: Start persistent background datastores and backend services"""
    print("\n[2/5] Recreating docker-compose development stack...")
    run_command(["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d"])

def get_mongo_password(context=None):
    """Safely extracts MongoDB password without brittle shell pipes or split failures."""
    cmd = ["docker"]
    if context:
        cmd.extend(["--context", context])
    cmd.extend(["exec", "mongodb", "env"])
    
    output = run_command(cmd, capture_output=True)
    for line in output.splitlines():
        if line.startswith("MONGO_INITDB_ROOT_PASSWORD="):
            # Split exactly once to prevent corruption if password contains '='
            return line.split("=", 1)[1].strip()
            
    raise ValueError(f"Could not find MONGO_INITDB_ROOT_PASSWORD in environment (context: {context or 'local'})")

def clone_production_data():
    """Step 3: Migrate production data securely to local DB"""
    print("\n[3/5] Cloning production seed data to local MongoDB...")
    
    try:
        prod_pass = get_mongo_password(context="prod-server")
    except Exception as e:
        print(f"Error extracting production password: {e}")
        print("Are you connected to the production server context ('docker context use prod-server')?")
        sys.exit(1)
        
    try:
        local_pass = get_mongo_password()
    except Exception as e:
        print("Warning: Could not extract local MongoDB password dynamically, falling back to default.")
        local_pass = "rootpassword"

    print(" - Dumping production database...")
    run_command([
        "docker", "--context", "prod-server", "exec", "mongodb", 
        "mongodump", "-u", "root", "-p", prod_pass, 
        "--authenticationDatabase", "admin", "--archive=/tmp/prod_dump.archive"
    ])
    
    print(" - Transferring archive...")
    scratch_dir = Path(os.environ.get("TEMP", "/tmp")) / "dedisalam_scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    archive_path = scratch_dir / "scratch_prod_dump.archive"
    
    run_command(["docker", "--context", "prod-server", "cp", "mongodb:/tmp/prod_dump.archive", str(archive_path)])
    run_command(["docker", "cp", str(archive_path), "mongodb:/tmp/prod_dump.archive"])
    
    print(" - Restoring to local development MongoDB...")
    run_command([
        "docker", "exec", "mongodb", 
        "mongorestore", "-u", "root", "-p", local_pass, 
        "--authenticationDatabase", "admin", "--archive=/tmp/prod_dump.archive", 
        "--nsInclude=user_db.*", "--nsInclude=notification_db.*", "--drop"
    ])
    
    print(" - Cleaning up temporary files...")
    if archive_path.exists():
        archive_path.unlink()
    run_command(["docker", "exec", "mongodb", "rm", "-f", "/tmp/prod_dump.archive"])
    run_command(["docker", "--context", "prod-server", "exec", "mongodb", "rm", "-f", "/tmp/prod_dump.archive"])

def verify_gateway_health():
    """Step 4: Check if backend services are healthy"""
    print("\n[4/5] Verifying Gateway Health...")
    time.sleep(5) # Allow microservices to initialize
    try:
        req = urllib.request.Request("http://localhost:3000/health")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                body = response.read().decode('utf-8')
                print(f"Gateway health check passed! ({body})")
            else:
                print(f"WARNING: Gateway returned non-200 status: {response.status}")
    except Exception as e:
        print(f"WARNING: Gateway health check failed. Please ensure backend is running. Error: {e}")

def verify_frontend_handoff():
    """Step 5: Clean up and verify frontend host prerequisites"""
    print("\n[5/5] Frontend Handoff Verification...")
    print(" - Checking frontend dev ports (4000, 4001, 4002)...")
    
    ports_in_use = []
    for port in [4000, 4001, 4002]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                ports_in_use.append(port)
    
    if ports_in_use:
        print(f" \033[93mWARNING: The following frontend ports are currently blocked: {ports_in_use}\033[0m")
        print(" Please terminate any running frontend dev servers before executing `npm run dev`.")
    else:
        print(" All frontend ports are free.")
        
    print(" - Pruning dangling docker images...")
    run_command(["docker", "image", "prune", "-f"])

def run():
    print("======================================================")
    print("   Frontend Development Environment Setup Script")
    print("======================================================")
    
    pull_images()
    recreate_dev_stack()
    clone_production_data()
    verify_gateway_health()
    verify_frontend_handoff()
    
    print("\n======================================================")
    print("Setup Complete!")
    print("Anda sekarang dapat menjalankan frontend secara lokal.")
    print("Dashboard: http://localhost:4000 (ng serve dashboard)")
    print("Landing:   http://localhost:4001 (ng serve landing)")
    print("Auth:      http://localhost:4002 (ng serve auth)")
    print("======================================================")

if __name__ == "__main__":
    run()
