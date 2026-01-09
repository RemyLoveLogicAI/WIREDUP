"""
Basic Agent Example
Simple agent implementation demonstrating core features.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.autowire import get_autowire, Scope
from src.config import get_config_loader


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BasicAgent:
    """Simple agent for demonstration"""
    
    def __init__(self, name: str, config: dict = None):
        self.name = name
        self.config = config or {}
        logger.info(f"Agent {name} initialized")
    
    async def execute(self, task: str) -> dict:
        """Execute a task"""
        logger.info(f"Agent {self.name} executing: {task}")
        
        # Simulate some processing
        await asyncio.sleep(1)
        
        result = {
            'agent': self.name,
            'task': task,
            'status': 'completed',
            'output': f"Processed: {task}"
        }
        
        logger.info(f"Agent {self.name} completed task")
        return result


async def main():
    """Main example function"""
    print("🚀 Basic Agent Example\n")
    
    # Initialize auto-wiring
    autowire = get_autowire()
    
    # Register agent
    autowire.register(
        name='basic_agent',
        factory=lambda: BasicAgent('basic_agent', {'version': '1.0'}),
        scope=Scope.SINGLETON
    )
    
    # Resolve agent
    agent = autowire.resolve('basic_agent')
    print(f"✅ Resolved agent: {agent.name}\n")
    
    # Execute tasks
    tasks = [
        "Analyze data",
        "Generate report",
        "Send notification"
    ]
    
    for task in tasks:
        result = await agent.execute(task)
        print(f"📊 Result: {result['status']} - {result['output']}\n")
    
    print("✅ Example completed!")


if __name__ == '__main__':
    asyncio.run(main())
