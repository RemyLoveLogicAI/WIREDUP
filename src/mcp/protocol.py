"""
Model Context Protocol (MCP) Integration
Advanced AI communication protocol implementation.
"""

import json
import logging
import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import threading
from queue import Queue


logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    STREAM = "stream"


class MCPRole(Enum):
    """MCP participant roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    AGENT = "agent"


@dataclass
class MCPMessage:
    """Model Context Protocol message"""
    id: str
    type: MCPMessageType
    role: MCPRole
    content: Union[str, Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['type'] = self.type.value
        data['role'] = self.role.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create from dictionary"""
        data['type'] = MCPMessageType(data['type'])
        data['role'] = MCPRole(data['role'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class MCPContext:
    """Conversation context for MCP"""
    session_id: str
    messages: List[MCPMessage] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: MCPMessage):
        """Add message to context"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_history(self, limit: Optional[int] = None) -> List[MCPMessage]:
        """Get message history"""
        if limit:
            return self.messages[-limit:]
        return self.messages.copy()
    
    def set_variable(self, key: str, value: Any):
        """Set context variable"""
        self.variables[key] = value
        self.updated_at = datetime.now()
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get context variable"""
        return self.variables.get(key, default)


class MCPHandler:
    """
    Handler interface for MCP messages.
    """
    
    def can_handle(self, message: MCPMessage, context: MCPContext) -> bool:
        """Check if handler can process this message"""
        raise NotImplementedError
    
    def handle(self, message: MCPMessage, context: MCPContext) -> Optional[MCPMessage]:
        """Handle the message and optionally return a response"""
        raise NotImplementedError


class MCPProtocol:
    """
    Model Context Protocol implementation.
    
    Features:
    - Message routing and handling
    - Context management
    - Tool/function calling
    - Streaming support
    - Error handling
    - Event hooks
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"mcp_{datetime.now().timestamp()}"
        self.context = MCPContext(session_id=self.session_id)
        self._handlers: List[MCPHandler] = []
        self._hooks: Dict[str, List[Callable]] = {
            'before_send': [],
            'after_send': [],
            'before_receive': [],
            'after_receive': [],
            'on_error': []
        }
        self._message_queue: Queue = Queue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        logger.info(f"MCPProtocol initialized (session={self.session_id})")
    
    def register_handler(self, handler: MCPHandler) -> 'MCPProtocol':
        """Register a message handler"""
        self._handlers.append(handler)
        logger.info(f"Registered handler: {handler.__class__.__name__}")
        return self
    
    def register_hook(self, event: str, callback: Callable) -> 'MCPProtocol':
        """Register an event hook"""
        if event in self._hooks:
            self._hooks[event].append(callback)
            logger.debug(f"Registered hook: {event}")
        return self
    
    def send(
        self,
        content: Union[str, Dict[str, Any]],
        role: MCPRole = MCPRole.USER,
        message_type: MCPMessageType = MCPMessageType.REQUEST,
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ) -> MCPMessage:
        """
        Send a message through the protocol.
        
        Args:
            content: Message content (text or structured data)
            role: Sender role
            message_type: Type of message
            metadata: Optional metadata
            parent_id: Optional parent message ID
        
        Returns:
            Created MCPMessage
        """
        # Create message
        message_id = f"msg_{len(self.context.messages)}_{datetime.now().timestamp()}"
        
        message = MCPMessage(
            id=message_id,
            type=message_type,
            role=role,
            content=content,
            metadata=metadata or {},
            parent_id=parent_id,
            context={'session_id': self.session_id}
        )
        
        # Execute before_send hooks
        self._execute_hooks('before_send', message, self.context)
        
        # Add to context
        self.context.add_message(message)
        
        # Execute after_send hooks
        self._execute_hooks('after_send', message, self.context)
        
        logger.debug(f"Sent message: {message.id} ({message.type.value})")
        
        return message
    
    def receive(self, message: MCPMessage) -> Optional[MCPMessage]:
        """
        Receive and process a message.
        
        Args:
            message: Incoming MCPMessage
        
        Returns:
            Optional response message
        """
        # Execute before_receive hooks
        self._execute_hooks('before_receive', message, self.context)
        
        # Add to context
        self.context.add_message(message)
        
        response = None
        
        try:
            # Find and execute handler
            for handler in self._handlers:
                if handler.can_handle(message, self.context):
                    logger.debug(f"Handler {handler.__class__.__name__} processing message {message.id}")
                    response = handler.handle(message, self.context)
                    break
            
            # Execute after_receive hooks
            self._execute_hooks('after_receive', message, self.context)
            
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            self._execute_hooks('on_error', e, message, self.context)
            
            # Create error response
            response = MCPMessage(
                id=f"err_{message.id}",
                type=MCPMessageType.ERROR,
                role=MCPRole.SYSTEM,
                content={'error': str(e), 'original_message_id': message.id},
                parent_id=message.id
            )
        
        return response
    
    def create_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        message_id: Optional[str] = None
    ) -> MCPMessage:
        """
        Create a tool call message.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            message_id: Optional message ID to respond to
        
        Returns:
            Tool call message
        """
        content = {
            'type': 'tool_call',
            'tool': tool_name,
            'parameters': parameters
        }
        
        return self.send(
            content=content,
            role=MCPRole.ASSISTANT,
            message_type=MCPMessageType.REQUEST,
            parent_id=message_id
        )
    
    def create_tool_response(
        self,
        tool_name: str,
        result: Any,
        message_id: str
    ) -> MCPMessage:
        """
        Create a tool response message.
        
        Args:
            tool_name: Name of the tool
            result: Tool execution result
            message_id: Original tool call message ID
        
        Returns:
            Tool response message
        """
        content = {
            'type': 'tool_response',
            'tool': tool_name,
            'result': result
        }
        
        return self.send(
            content=content,
            role=MCPRole.TOOL,
            message_type=MCPMessageType.RESPONSE,
            parent_id=message_id
        )
    
    def get_context(self) -> MCPContext:
        """Get current context"""
        return self.context
    
    def get_history(self, limit: Optional[int] = None, role: Optional[MCPRole] = None) -> List[MCPMessage]:
        """
        Get message history with optional filtering.
        
        Args:
            limit: Maximum number of messages
            role: Filter by role
        
        Returns:
            List of messages
        """
        messages = self.context.get_history(limit)
        
        if role:
            messages = [m for m in messages if m.role == role]
        
        return messages
    
    def export_context(self) -> Dict[str, Any]:
        """Export context as dictionary"""
        return {
            'session_id': self.session_id,
            'messages': [m.to_dict() for m in self.context.messages],
            'variables': self.context.variables,
            'metadata': self.context.metadata,
            'created_at': self.context.created_at.isoformat(),
            'updated_at': self.context.updated_at.isoformat()
        }
    
    def import_context(self, data: Dict[str, Any]):
        """Import context from dictionary"""
        self.session_id = data['session_id']
        self.context = MCPContext(
            session_id=data['session_id'],
            messages=[MCPMessage.from_dict(m) for m in data['messages']],
            variables=data['variables'],
            metadata=data['metadata'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
        logger.info(f"Imported context: {self.session_id}")
    
    def clear_context(self, keep_variables: bool = False):
        """Clear context"""
        variables = self.context.variables if keep_variables else {}
        self.context = MCPContext(session_id=self.session_id, variables=variables)
        logger.info("Context cleared")
    
    def _execute_hooks(self, event: str, *args):
        """Execute event hooks"""
        for hook in self._hooks.get(event, []):
            try:
                hook(*args)
            except Exception as e:
                logger.error(f"Hook error ({event}): {e}")


# Example handler implementations

class EchoHandler(MCPHandler):
    """Simple echo handler for testing"""
    
    def can_handle(self, message: MCPMessage, context: MCPContext) -> bool:
        return (
            message.type == MCPMessageType.REQUEST and
            isinstance(message.content, str) and
            message.content.startswith('/echo')
        )
    
    def handle(self, message: MCPMessage, context: MCPContext) -> MCPMessage:
        content = message.content[6:].strip()  # Remove '/echo '
        
        return MCPMessage(
            id=f"echo_{message.id}",
            type=MCPMessageType.RESPONSE,
            role=MCPRole.ASSISTANT,
            content=f"Echo: {content}",
            parent_id=message.id
        )


class ContextVariableHandler(MCPHandler):
    """Handler for setting/getting context variables"""
    
    def can_handle(self, message: MCPMessage, context: MCPContext) -> bool:
        if message.type != MCPMessageType.REQUEST:
            return False
        
        if isinstance(message.content, dict):
            return message.content.get('type') in ('set_variable', 'get_variable')
        
        return False
    
    def handle(self, message: MCPMessage, context: MCPContext) -> MCPMessage:
        content = message.content
        action = content.get('type')
        
        if action == 'set_variable':
            key = content.get('key')
            value = content.get('value')
            context.set_variable(key, value)
            response_content = {'status': 'success', 'key': key}
        
        elif action == 'get_variable':
            key = content.get('key')
            value = context.get_variable(key)
            response_content = {'status': 'success', 'key': key, 'value': value}
        
        else:
            response_content = {'status': 'error', 'message': 'Unknown action'}
        
        return MCPMessage(
            id=f"var_{message.id}",
            type=MCPMessageType.RESPONSE,
            role=MCPRole.SYSTEM,
            content=response_content,
            parent_id=message.id
        )
