"""
SSH Management and Secure Connection System
Advanced SSH connection pooling, key management, and secure execution.
"""

import logging
import paramiko
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time
from queue import Queue, Empty


logger = logging.getLogger(__name__)


@dataclass
class SSHCredentials:
    """SSH connection credentials"""
    host: str
    port: int = 22
    username: str = ""
    password: Optional[str] = None
    key_filename: Optional[str] = None
    passphrase: Optional[str] = None
    timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary (masking sensitive data)"""
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': '***' if self.password else None,
            'key_filename': self.key_filename,
            'timeout': self.timeout
        }


@dataclass
class SSHConnection:
    """SSH connection wrapper"""
    credentials: SSHCredentials
    client: paramiko.SSHClient
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    use_count: int = 0
    is_alive: bool = True
    
    def mark_used(self):
        """Mark connection as used"""
        self.last_used = datetime.now()
        self.use_count += 1
    
    def is_expired(self, max_age: int = 3600) -> bool:
        """Check if connection has expired"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > max_age
    
    def is_idle(self, idle_timeout: int = 300) -> bool:
        """Check if connection has been idle too long"""
        idle = (datetime.now() - self.last_used).total_seconds()
        return idle > idle_timeout


@dataclass
class SSHExecutionResult:
    """Result of SSH command execution"""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    host: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def success(self) -> bool:
        """Check if command succeeded"""
        return self.exit_code == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary"""
        return {
            'command': self.command,
            'exit_code': self.exit_code,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'duration': self.duration,
            'host': self.host,
            'success': self.success,
            'timestamp': self.timestamp.isoformat()
        }


class SSHConnectionPool:
    """
    Thread-safe SSH connection pool with automatic cleanup.
    """
    
    def __init__(
        self,
        max_connections: int = 10,
        max_age: int = 3600,
        idle_timeout: int = 300,
        cleanup_interval: int = 60
    ):
        self.max_connections = max_connections
        self.max_age = max_age
        self.idle_timeout = idle_timeout
        self.cleanup_interval = cleanup_interval
        
        self._pools: Dict[str, List[SSHConnection]] = {}
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        
        logger.info(f"SSHConnectionPool initialized (max={max_connections})")
    
    def start_cleanup(self):
        """Start automatic cleanup thread"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info("SSH connection cleanup started")
    
    def stop_cleanup(self):
        """Stop cleanup thread"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        logger.info("SSH connection cleanup stopped")
    
    def get_connection(self, credentials: SSHCredentials) -> SSHConnection:
        """
        Get a connection from the pool or create a new one.
        
        Args:
            credentials: SSH credentials
        
        Returns:
            SSHConnection instance
        """
        with self._lock:
            pool_key = f"{credentials.username}@{credentials.host}:{credentials.port}"
            
            # Get or create pool for this host
            if pool_key not in self._pools:
                self._pools[pool_key] = []
            
            pool = self._pools[pool_key]
            
            # Try to find available connection
            for conn in pool:
                if conn.is_alive and not conn.is_expired(self.max_age):
                    try:
                        # Test connection
                        transport = conn.client.get_transport()
                        if transport and transport.is_active():
                            conn.mark_used()
                            logger.debug(f"Reusing SSH connection to {pool_key}")
                            return conn
                    except Exception:
                        conn.is_alive = False
            
            # Create new connection if under limit
            if len([c for c in pool if c.is_alive]) < self.max_connections:
                conn = self._create_connection(credentials)
                pool.append(conn)
                logger.info(f"Created new SSH connection to {pool_key}")
                return conn
            
            # Wait for available connection
            logger.warning(f"Connection pool full for {pool_key}, waiting...")
            time.sleep(1)
            return self.get_connection(credentials)
    
    def release_connection(self, connection: SSHConnection):
        """Release connection back to pool"""
        # Connection remains in pool for reuse
        logger.debug(f"Released SSH connection to {connection.credentials.host}")
    
    def close_all(self):
        """Close all connections"""
        with self._lock:
            for pool in self._pools.values():
                for conn in pool:
                    try:
                        conn.client.close()
                    except Exception as e:
                        logger.error(f"Error closing connection: {e}")
            
            self._pools.clear()
            logger.info("All SSH connections closed")
    
    def _create_connection(self, credentials: SSHCredentials) -> SSHConnection:
        """Create a new SSH connection"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            connect_kwargs = {
                'hostname': credentials.host,
                'port': credentials.port,
                'username': credentials.username,
                'timeout': credentials.timeout
            }
            
            if credentials.key_filename:
                connect_kwargs['key_filename'] = credentials.key_filename
                if credentials.passphrase:
                    connect_kwargs['passphrase'] = credentials.passphrase
            elif credentials.password:
                connect_kwargs['password'] = credentials.password
            
            client.connect(**connect_kwargs)
            
            return SSHConnection(
                credentials=credentials,
                client=client
            )
        
        except Exception as e:
            logger.error(f"Failed to create SSH connection to {credentials.host}: {e}")
            raise
    
    def _cleanup_worker(self):
        """Background worker to cleanup expired connections"""
        while self._running:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
    
    def _cleanup_expired(self):
        """Remove expired and idle connections"""
        with self._lock:
            for pool_key, pool in list(self._pools.items()):
                cleaned = []
                
                for conn in pool:
                    if conn.is_expired(self.max_age) or conn.is_idle(self.idle_timeout):
                        try:
                            conn.client.close()
                            logger.debug(f"Cleaned up expired connection to {pool_key}")
                        except Exception:
                            pass
                    else:
                        cleaned.append(conn)
                
                self._pools[pool_key] = cleaned
                
                # Remove empty pools
                if not cleaned:
                    del self._pools[pool_key]


class SSHManager:
    """
    Advanced SSH Management System.
    
    Features:
    - Connection pooling
    - Command execution with retries
    - File transfer (SCP/SFTP)
    - Secure key management
    - Command templating
    - Parallel execution
    """
    
    def __init__(
        self,
        connection_pool: Optional[SSHConnectionPool] = None,
        default_credentials: Optional[SSHCredentials] = None
    ):
        self.pool = connection_pool or SSHConnectionPool()
        self.default_credentials = default_credentials
        self._lock = threading.RLock()
        
        logger.info("SSHManager initialized")
        
        # Start connection pool cleanup
        self.pool.start_cleanup()
    
    def execute(
        self,
        command: str,
        credentials: Optional[SSHCredentials] = None,
        timeout: int = 30,
        retries: int = 0,
        raise_on_error: bool = False
    ) -> SSHExecutionResult:
        """
        Execute a command via SSH.
        
        Args:
            command: Command to execute
            credentials: SSH credentials (uses default if not provided)
            timeout: Command timeout in seconds
            retries: Number of retries on failure
            raise_on_error: Raise exception on non-zero exit code
        
        Returns:
            SSHExecutionResult
        """
        creds = credentials or self.default_credentials
        if not creds:
            raise ValueError("No SSH credentials provided")
        
        attempt = 0
        last_error = None
        
        while attempt <= retries:
            try:
                start_time = time.time()
                
                # Get connection from pool
                connection = self.pool.get_connection(creds)
                
                # Execute command
                stdin, stdout, stderr = connection.client.exec_command(
                    command,
                    timeout=timeout
                )
                
                # Wait for completion
                exit_code = stdout.channel.recv_exit_status()
                stdout_data = stdout.read().decode('utf-8')
                stderr_data = stderr.read().decode('utf-8')
                
                duration = time.time() - start_time
                
                # Release connection
                self.pool.release_connection(connection)
                
                # Create result
                result = SSHExecutionResult(
                    command=command,
                    exit_code=exit_code,
                    stdout=stdout_data,
                    stderr=stderr_data,
                    duration=duration,
                    host=creds.host
                )
                
                logger.info(f"SSH command executed on {creds.host}: {command} (exit={exit_code})")
                
                if not result.success and raise_on_error:
                    raise RuntimeError(f"Command failed with exit code {exit_code}: {stderr_data}")
                
                return result
            
            except Exception as e:
                last_error = e
                attempt += 1
                
                if attempt <= retries:
                    logger.warning(f"SSH execution failed (attempt {attempt}/{retries + 1}): {e}")
                    time.sleep(1)
                else:
                    logger.error(f"SSH execution failed after {retries + 1} attempts: {e}")
                    if raise_on_error:
                        raise
                    
                    return SSHExecutionResult(
                        command=command,
                        exit_code=-1,
                        stdout="",
                        stderr=str(last_error),
                        duration=0,
                        host=creds.host
                    )
    
    def execute_batch(
        self,
        commands: List[str],
        credentials: Optional[SSHCredentials] = None,
        parallel: bool = False
    ) -> List[SSHExecutionResult]:
        """
        Execute multiple commands.
        
        Args:
            commands: List of commands to execute
            credentials: SSH credentials
            parallel: Execute in parallel
        
        Returns:
            List of SSHExecutionResult
        """
        if parallel:
            results = []
            threads = []
            
            def worker(cmd):
                result = self.execute(cmd, credentials)
                results.append(result)
            
            for cmd in commands:
                thread = threading.Thread(target=worker, args=(cmd,))
                thread.start()
                threads.append(thread)
            
            for thread in threads:
                thread.join()
            
            return results
        else:
            return [self.execute(cmd, credentials) for cmd in commands]
    
    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        credentials: Optional[SSHCredentials] = None
    ) -> bool:
        """
        Upload file via SFTP.
        
        Args:
            local_path: Local file path
            remote_path: Remote file path
            credentials: SSH credentials
        
        Returns:
            True if successful
        """
        creds = credentials or self.default_credentials
        if not creds:
            raise ValueError("No SSH credentials provided")
        
        try:
            connection = self.pool.get_connection(creds)
            sftp = connection.client.open_sftp()
            
            sftp.put(str(local_path), remote_path)
            sftp.close()
            
            self.pool.release_connection(connection)
            
            logger.info(f"Uploaded file to {creds.host}:{remote_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def download_file(
        self,
        remote_path: str,
        local_path: Path,
        credentials: Optional[SSHCredentials] = None
    ) -> bool:
        """
        Download file via SFTP.
        
        Args:
            remote_path: Remote file path
            local_path: Local file path
            credentials: SSH credentials
        
        Returns:
            True if successful
        """
        creds = credentials or self.default_credentials
        if not creds:
            raise ValueError("No SSH credentials provided")
        
        try:
            connection = self.pool.get_connection(creds)
            sftp = connection.client.open_sftp()
            
            sftp.get(remote_path, str(local_path))
            sftp.close()
            
            self.pool.release_connection(connection)
            
            logger.info(f"Downloaded file from {creds.host}:{remote_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def close(self):
        """Close all connections"""
        self.pool.stop_cleanup()
        self.pool.close_all()
        logger.info("SSHManager closed")
