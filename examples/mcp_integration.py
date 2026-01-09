"""
MCP Integration Example
Demonstrates Model Context Protocol usage.
"""

import asyncio
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp import MCPProtocol, MCPRole, MCPMessageType, MCPHandler, MCPMessage, MCPContext


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskHandler(MCPHandler):
    """Handler for task execution requests"""
    
    def can_handle(self, message: MCPMessage, context: MCPContext) -> bool:
        return (
            message.type == MCPMessageType.REQUEST and
            isinstance(message.content, dict) and
            message.content.get('type') == 'execute_task'
        )
    
    def handle(self, message: MCPMessage, context: MCPContext) -> MCPMessage:
        """Handle task execution"""
        task = message.content.get('task')
        logger.info(f"Executing task: {task}")
        
        # Simulate task execution
        result = f"Completed: {task}"
        
        return MCPMessage(
            id=f"resp_{message.id}",
            type=MCPMessageType.RESPONSE,
            role=MCPRole.ASSISTANT,
            content={
                'type': 'task_result',
                'task': task,
                'result': result,
                'status': 'success'
            },
            parent_id=message.id
        )


async def main():
    """Main example function"""
    print("🔌 MCP Integration Example\n")
    
    # Create MCP protocol
    mcp = MCPProtocol(session_id="example_session")
    
    # Register handler
    mcp.register_handler(TaskHandler())
    
    # Register hooks
    mcp.register_hook('before_send', lambda msg, ctx: 
        logger.info(f"Sending message: {msg.id}")
    )
    mcp.register_hook('after_receive', lambda msg, ctx:
        logger.info(f"Received message: {msg.id}")
    )
    
    print("✅ MCP Protocol initialized\n")
    
    # Send request
    request = mcp.send(
        content={
            'type': 'execute_task',
            'task': 'Analyze data'
        },
        role=MCPRole.USER,
        message_type=MCPMessageType.REQUEST
    )
    
    print(f"📤 Sent request: {request.id}")
    print(f"   Content: {request.content}\n")
    
    # Process request
    response = mcp.receive(request)
    
    if response:
        print(f"📥 Received response: {response.id}")
        print(f"   Content: {response.content}\n")
    
    # Get message history
    history = mcp.get_history()
    print(f"📊 Message history: {len(history)} messages")
    
    # Export context
    context_data = mcp.export_context()
    print(f"\n💾 Context exported:")
    print(f"   Session: {context_data['session_id']}")
    print(f"   Messages: {len(context_data['messages'])}")
    
    print("\n✅ Example completed!")


if __name__ == '__main__':
    asyncio.run(main())
