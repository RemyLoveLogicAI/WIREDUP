"""
SSH Deployment Example
Demonstrates remote deployment via SSH.
"""

import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ssh import SSHManager, SSHCredentials


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main example function"""
    print("🔒 SSH Deployment Example\n")
    
    # Note: Update these with your actual SSH credentials
    credentials = SSHCredentials(
        host='localhost',  # Change to your host
        port=22,
        username='user',   # Change to your username
        # Use either password or key_filename
        # password='your_password',
        key_filename=str(Path.home() / '.ssh' / 'id_rsa'),
        timeout=30
    )
    
    print(f"🔐 Connecting to {credentials.host}...")
    
    # Create SSH manager
    manager = SSHManager()
    
    try:
        # Execute single command
        print("\n📤 Executing: ls -la")
        result = manager.execute('ls -la', credentials=credentials)
        
        if result.success:
            print("✅ Command succeeded")
            print(f"\nOutput:\n{result.stdout}")
        else:
            print(f"❌ Command failed: {result.stderr}")
        
        # Execute batch commands
        print("\n📤 Executing batch commands...")
        commands = [
            'pwd',
            'whoami',
            'date',
            'uname -a'
        ]
        
        results = manager.execute_batch(commands, credentials=credentials)
        
        print("\n📊 Batch Results:")
        for i, result in enumerate(results):
            status = "✅" if result.success else "❌"
            print(f"{status} {commands[i]}: {result.stdout.strip()}")
        
        # File operations (example - commented out)
        print("\n📁 File Operations Example:")
        print("   (Update paths and uncomment to test)")
        
        # Upload example
        # local_file = Path(__file__)
        # remote_path = f'/tmp/{local_file.name}'
        # if manager.upload_file(local_file, remote_path, credentials):
        #     print(f"✅ Uploaded {local_file} to {remote_path}")
        
        # Download example
        # if manager.download_file('/etc/hostname', Path('/tmp/hostname'), credentials):
        #     print("✅ Downloaded /etc/hostname")
        
        print("\n✅ Example completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # Cleanup
        manager.close()
        print("\n🔌 Connections closed")


if __name__ == '__main__':
    main()
