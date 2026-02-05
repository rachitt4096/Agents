"""
File Manager - Handle file operations safely
"""
import os
from pathlib import Path
from typing import Optional, List
from config.settings import settings
from config.models import ActionResult, ActionType
from loguru import logger


class FileManager:
    """Manage file operations in workspace"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = Path(workspace_dir or settings.WORKSPACE_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    def _is_safe_path(self, filepath: Path) -> tuple[bool, Optional[str]]:
        """Check if path is within workspace"""
        try:
            abs_path = (self.workspace_dir / filepath).resolve()
            if not str(abs_path).startswith(str(self.workspace_dir.resolve())):
                return False, "Path outside workspace not allowed"
            return True, None
        except Exception as e:
            return False, str(e)
    
    def write_file(
        self,
        filename: str,
        content: str,
        overwrite: bool = False
    ) -> ActionResult:
        """
        Write content to file
        
        Args:
            filename: File to write
            content: Content to write
            overwrite: Allow overwriting existing files
            
        Returns:
            ActionResult with file path
        """
        logger.info(f"Writing file: {filename}")
        
        try:
            filepath = Path(filename)
            
            # Safety check
            is_safe, reason = self._is_safe_path(filepath)
            if not is_safe:
                return ActionResult(
                    action_type=ActionType.FILE_WRITE,
                    success=False,
                    error=f"Unsafe path: {reason}"
                )
            
            full_path = self.workspace_dir / filepath
            
            # Check if file exists
            if full_path.exists() and not overwrite:
                return ActionResult(
                    action_type=ActionType.FILE_WRITE,
                    success=False,
                    error=f"File exists: {filename} (use overwrite=True)"
                )
            
            # Check content size
            if len(content.encode()) > self.max_file_size:
                return ActionResult(
                    action_type=ActionType.FILE_WRITE,
                    success=False,
                    error=f"Content too large (max {settings.MAX_FILE_SIZE_MB}MB)"
                )
            
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            full_path.write_text(content)
            
            logger.success(f"File written: {full_path}")
            
            return ActionResult(
                action_type=ActionType.FILE_WRITE,
                success=True,
                output=f"File written: {full_path}",
                files_created=[str(full_path)],
                metadata={
                    "size_bytes": len(content.encode()),
                    "lines": content.count('\n') + 1
                }
            )
            
        except Exception as e:
            logger.error(f"File write error: {e}")
            return ActionResult(
                action_type=ActionType.FILE_WRITE,
                success=False,
                error=str(e)
            )
    
    def read_file(self, filename: str) -> ActionResult:
        """Read file content"""
        logger.info(f"Reading file: {filename}")
        
        try:
            filepath = Path(filename)
            
            # Safety check
            is_safe, reason = self._is_safe_path(filepath)
            if not is_safe:
                return ActionResult(
                    action_type=ActionType.FILE_READ,
                    success=False,
                    error=f"Unsafe path: {reason}"
                )
            
            full_path = self.workspace_dir / filepath
            
            if not full_path.exists():
                return ActionResult(
                    action_type=ActionType.FILE_READ,
                    success=False,
                    error=f"File not found: {filename}"
                )
            
            # Check file size
            if full_path.stat().st_size > self.max_file_size:
                return ActionResult(
                    action_type=ActionType.FILE_READ,
                    success=False,
                    error=f"File too large to read"
                )
            
            content = full_path.read_text()
            
            return ActionResult(
                action_type=ActionType.FILE_READ,
                success=True,
                output=content,
                metadata={
                    "size_bytes": full_path.stat().st_size,
                    "lines": content.count('\n') + 1
                }
            )
            
        except Exception as e:
            logger.error(f"File read error: {e}")
            return ActionResult(
                action_type=ActionType.FILE_READ,
                success=False,
                error=str(e)
            )
    
    def list_files(self, pattern: str = "*") -> ActionResult:
        """List files in workspace"""
        try:
            files = list(self.workspace_dir.glob(pattern))
            file_list = [str(f.relative_to(self.workspace_dir)) for f in files]
            
            return ActionResult(
                action_type=ActionType.FILE_READ,
                success=True,
                output="\n".join(file_list),
                metadata={
                    "count": len(file_list),
                    "pattern": pattern
                }
            )
            
        except Exception as e:
            return ActionResult(
                action_type=ActionType.FILE_READ,
                success=False,
                error=str(e)
            )
    
    def create_directory(self, dirname: str) -> ActionResult:
        """Create directory in workspace"""
        try:
            dirpath = self.workspace_dir / dirname
            dirpath.mkdir(parents=True, exist_ok=True)
            
            return ActionResult(
                action_type=ActionType.FILE_WRITE,
                success=True,
                output=f"Directory created: {dirpath}"
            )
            
        except Exception as e:
            return ActionResult(
                action_type=ActionType.FILE_WRITE,
                success=False,
                error=str(e)
            )