#!/usr/bin/env python3
"""
CLI Demo - Interactive command-line interface for the orchestrator
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import MultiAgentOrchestrator
from config.settings import settings
from loguru import logger
import argparse


def setup_logging():
    """Configure logging"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=settings.LOG_LEVEL
    )
    logger.add(
        settings.LOG_FILE,
        rotation="10 MB",
        retention="7 days",
        level=settings.LOG_LEVEL
    )


def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║         Multi-Agent Orchestrator - CLI Demo                      ║
║         Autonomous Task Execution with AI Agents                 ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_objective_result(objective):
    """Pretty print objective results"""
    print("\n" + "="*80)
    print(f"OBJECTIVE: {objective.description}")
    print("="*80)
    print(f"\nStatus: {objective.status}")
    print(f"Tasks: {len(objective.tasks)}")
    print(f"Completed: {sum(1 for t in objective.tasks if t.status == 'completed')}")
    print(f"Failed: {sum(1 for t in objective.tasks if t.status == 'failed')}")
    
    print("\n" + "-"*80)
    print("TASKS:")
    print("-"*80)
    
    for i, task in enumerate(objective.tasks, 1):
        status_emoji = "✅" if task.status == "completed" else "❌"
        print(f"\n{status_emoji} Task {i}: {task.description}")
        print(f"   Agent: {task.agent_type}")
        print(f"   Status: {task.status}")
        if task.retry_count > 0:
            print(f"   Retries: {task.retry_count}")
    
    print("\n" + "="*80)
    print("FINAL RESULT:")
    print("="*80)
    print(objective.final_result)
    print("="*80 + "\n")


def run_demo_simple():
    """Run simple demo"""
    print_banner()
    print("Running Simple Demo...\n")
    
    orchestrator = MultiAgentOrchestrator()
    
    objective = orchestrator.execute_objective(
        "Explain the key benefits of microservices architecture in 3 points"
    )
    
    print_objective_result(objective)


def run_demo_complex():
    """Run complex demo"""
    print_banner()
    print("Running Complex Demo...\n")
    
    orchestrator = MultiAgentOrchestrator()
    
    objective = orchestrator.execute_objective(
        "Research the current state of AI agents, analyze the key trends, "
        "and provide recommendations for building an AI agent system"
    )
    
    print_objective_result(objective)
    
    # Print stats
    stats = orchestrator.get_stats()
    print("\n" + "="*80)
    print("STATISTICS:")
    print("="*80)
    print(f"Total API calls: {stats['llm_stats']['total_calls']}")
    print(f"Total tokens: {stats['llm_stats']['total_tokens']}")
    print("="*80 + "\n")


def run_interactive():
    """Run interactive mode"""
    print_banner()
    print("Interactive Mode - Enter objectives (type 'quit' to exit)\n")
    
    orchestrator = MultiAgentOrchestrator()
    
    while True:
        try:
            objective_desc = input("\n📋 Enter objective: ").strip()
            
            if objective_desc.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye! 👋\n")
                break
            
            if not objective_desc:
                continue
            
            # Execute objective
            objective = orchestrator.execute_objective(objective_desc)
            print_objective_result(objective)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋\n")
            break
        except Exception as e:
            logger.error(f"Error: {e}")


def run_custom(objective_text: str):
    """Run custom objective"""
    print_banner()
    print(f"Executing custom objective...\n")
    
    orchestrator = MultiAgentOrchestrator()
    objective = orchestrator.execute_objective(objective_text)
    print_objective_result(objective)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Orchestrator CLI Demo"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["simple", "complex", "interactive", "custom"],
        default="interactive",
        help="Demo mode to run"
    )
    parser.add_argument(
        "--objective",
        "-o",
        type=str,
        help="Custom objective text (for custom mode)"
    )
    
    args = parser.parse_args()
    
    # Check API key
    if not settings.GROQ_API_KEY:
        print("\n❌ Error: GROQ_API_KEY not found!")
        print("\nTo get started:")
        print("1. Visit https://console.groq.com")
        print("2. Sign up for free account")
        print("3. Generate API key")
        print("4. Set environment variable: export GROQ_API_KEY='your-key'")
        print("5. Or create .env file with: GROQ_API_KEY=your-key\n")
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    
    # Run appropriate mode
    if args.mode == "simple":
        run_demo_simple()
    elif args.mode == "complex":
        run_demo_complex()
    elif args.mode == "interactive":
        run_interactive()
    elif args.mode == "custom":
        if not args.objective:
            print("❌ Error: --objective required for custom mode")
            sys.exit(1)
        run_custom(args.objective)


if __name__ == "__main__":
    main()