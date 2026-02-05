"""
Streamlit UI for Action-Oriented Multi-Agent System
WITH LIVE TERMINAL OUTPUT AND FILE DOWNLOADS!
"""
import streamlit as st
import sys
from pathlib import Path
import time
from datetime import datetime
import zipfile
import io

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import ActionOrchestrator
from config.settings import settings
from loguru import logger

# Configure page
st.set_page_config(
    page_title="🤖 Action Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .terminal {
        background-color: #1e1e1e;
        color: #00ff00;
        font-family: 'Courier New', monospace;
        padding: 15px;
        border-radius: 5px;
        height: 400px;
        overflow-y: auto;
        margin: 10px 0;
    }
    .terminal-line {
        margin: 2px 0;
        font-size: 13px;
    }
    .status-running {
        color: #ffa500;
    }
    .status-success {
        color: #00ff00;
    }
    .status-error {
        color: #ff0000;
    }
    .file-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'terminal_output' not in st.session_state:
    st.session_state.terminal_output = []
if 'current_objective' not in st.session_state:
    st.session_state.current_objective = None
if 'execution_history' not in st.session_state:
    st.session_state.execution_history = []
if 'files_created' not in st.session_state:
    st.session_state.files_created = []

def add_terminal_line(message: str, type: str = "info"):
    """Add line to terminal output"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    emoji = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "action": "⚡",
        "file": "📄"
    }.get(type, "•")
    
    st.session_state.terminal_output.append({
        "timestamp": timestamp,
        "message": message,
        "type": type,
        "emoji": emoji
    })

def progress_callback(update: dict):
    """Callback for orchestrator progress"""
    msg_type = update.get("type", "status")
    message = update.get("message", "")
    
    # Map update types to terminal types
    type_mapping = {
        "objective_start": "info",
        "decomposing": "info",
        "tasks_created": "success",
        "task_start": "info",
        "executing": "action",
        "action_complete": "success",
        "action_failed": "error",
        "task_complete": "success",
        "task_failed": "error",
        "objective_complete": "success"
    }
    
    terminal_type = type_mapping.get(msg_type, "info")
    add_terminal_line(message, terminal_type)

def create_zip_of_files(files: list) -> bytes:
    """Create zip file of generated files"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in files:
            if Path(file_path).exists():
                zip_file.write(file_path, Path(file_path).name)
    return zip_buffer.getvalue()

# ============================================================================
# MAIN APP
# ============================================================================

# Header
st.title("🤖 Action-Oriented Multi-Agent System")
st.markdown("### Execute objectives with REAL actions - code execution, file creation, command running!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key check
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        st.error("❌ GROQ_API_KEY not configured!")
        st.info("Add your API key to .env file")
        st.stop()
    else:
        st.success("✅ API Key configured")
    
    st.markdown("---")
    
    # Settings
    st.subheader("🎛️ Execution Settings")
    enable_code = st.checkbox("Enable Code Execution", value=settings.ENABLE_CODE_EXECUTION)
    enable_shell = st.checkbox("Enable Shell Commands", value=settings.ENABLE_SHELL_COMMANDS)
    enable_files = st.checkbox("Enable File Operations", value=settings.ENABLE_FILE_OPERATIONS)
    
    st.markdown("---")
    
    # Examples
    st.subheader("💡 Example Objectives")
    examples = [
        "Create a Python script that calculates fibonacci numbers and save it to fib.py",
        "Write a data analysis script that generates random data and plots it",
        "Create a simple web scraper and save it to scraper.py",
        "Generate a JSON file with 10 sample user records",
        "Write a calculator program and test it with calculations"
    ]
    
    for ex in examples:
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state.example_objective = ex

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🎯 Enter Objective")
    
    # Objective input
    objective_text = st.text_area(
        "What do you want the agents to do?",
        value=st.session_state.get('example_objective', ''),
        height=150,
        placeholder="Example: Create a Python script that generates a CSV file with 100 rows of random data..."
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        execute_btn = st.button("🚀 Execute", type="primary", use_container_width=True)
    with col_btn2:
        clear_terminal = st.button("🗑️ Clear Terminal", use_container_width=True)
    with col_btn3:
        if st.session_state.files_created:
            download_all = st.button("📦 Download All Files", use_container_width=True)
        else:
            download_all = False
    
    # Execute objective
    if execute_btn and objective_text:
        st.session_state.terminal_output = []
        st.session_state.files_created = []
        
        with st.spinner("🤖 Agents are working..."):
            try:
                # Initialize orchestrator with progress callback
                orchestrator = ActionOrchestrator(progress_callback=progress_callback)
                
                # Execute
                add_terminal_line("="*60, "info")
                objective = orchestrator.execute_objective(objective_text)
                add_terminal_line("="*60, "info")
                
                # Store results
                st.session_state.current_objective = objective
                st.session_state.files_created = objective.files_generated
                st.session_state.execution_history.append({
                    "timestamp": datetime.now(),
                    "objective": objective_text,
                    "status": objective.status,
                    "files": len(objective.files_generated)
                })
                
                st.success(f"✅ Objective {objective.status}!")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                add_terminal_line(f"ERROR: {str(e)}", "error")
    
    # Clear terminal
    if clear_terminal:
        st.session_state.terminal_output = []
        st.rerun()
    
    # Download all files
    if download_all and st.session_state.files_created:
        zip_data = create_zip_of_files(st.session_state.files_created)
        st.download_button(
            label="📥 Download ZIP",
            data=zip_data,
            file_name=f"agent_outputs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )

with col2:
    st.header("🖥️ Live Terminal")
    
    # Terminal output
    terminal_html = '<div class="terminal">'
    
    if st.session_state.terminal_output:
        for line in st.session_state.terminal_output[-50:]:  # Show last 50 lines
            timestamp = line['timestamp']
            message = line['message']
            emoji = line['emoji']
            terminal_html += f'<div class="terminal-line">[{timestamp}] {emoji} {message}</div>'
    else:
        terminal_html += '<div class="terminal-line">🟢 Terminal ready. Waiting for objective...</div>'
    
    terminal_html += '</div>'
    st.markdown(terminal_html, unsafe_allow_html=True)

# Results section
if st.session_state.current_objective:
    st.markdown("---")
    st.header("📊 Results")
    
    obj = st.session_state.current_objective
    
    # Stats
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Status", obj.status.upper())
    with col_stat2:
        completed = sum(1 for t in obj.tasks if t.status == "completed")
        st.metric("Tasks", f"{completed}/{len(obj.tasks)}")
    with col_stat3:
        st.metric("Actions", len(obj.actions_executed))
    with col_stat4:
        st.metric("Files", len(obj.files_generated))
    
    # Files created
    if obj.files_generated:
        st.subheader("📁 Generated Files")
        
        for file_path in obj.files_generated:
            with st.expander(f"📄 {Path(file_path).name}"):
                col_file1, col_file2 = st.columns([3, 1])
                
                with col_file1:
                    try:
                        content = Path(file_path).read_text()
                        st.code(content, language="python" if file_path.endswith(".py") else None)
                    except:
                        st.warning("Cannot preview file")
                
                with col_file2:
                    try:
                        file_data = Path(file_path).read_bytes()
                        st.download_button(
                            "📥 Download",
                            file_data,
                            file_name=Path(file_path).name,
                            key=f"download_{file_path}"
                        )
                    except:
                        st.error("Cannot download")
    
    # Detailed results
    with st.expander("📋 Detailed Results", expanded=False):
        st.markdown(obj.final_result)

# Execution History
if st.session_state.execution_history:
    st.markdown("---")
    st.header("📜 Execution History")
    
    for i, hist in enumerate(reversed(st.session_state.execution_history[-10:]), 1):
        with st.expander(f"{hist['timestamp'].strftime('%H:%M:%S')} - {hist['objective'][:60]}..."):
            st.write(f"**Status:** {hist['status']}")
            st.write(f"**Files Created:** {hist['files']}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🤖 Action-Oriented Multi-Agent System | Powered by Groq LLaMA 3.1</p>
    <p>This system can execute REAL code, run commands, and create files!</p>
</div>
""", unsafe_allow_html=True)