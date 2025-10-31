"""
File handling utilities for data extraction
"""

import pandas as pd
import glob
import datetime
import shutil
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import os

from ..utils.logging import setup_logger


class FileHandler:
    """Handle file operations for solar plant data"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    def find_files_by_date(
        self,
        source_dir: str,
        year: int,
        month: int,
        container: str,
        partial_month: bool = False,
        first_day: int = 1,
        last_day: int = 31
    ) -> List[str]:
        """
        Find files in directory by date criteria
        
        Args:
            source_dir: Source directory
            year: Target year
            month: Target month
            container: File container/pattern to match
            partial_month: Whether to filter by day range
            first_day: First day of range (if partial_month)
            last_day: Last day of range (if partial_month)
        
        Returns:
            List of matching file paths
        """
        all_files = glob.glob(os.path.join(source_dir, "*.csv"))
        valid_files = []
        
        self.logger.info(f"Searching for files in {source_dir} for {year}/{month:02d}")
        
        for file_path in all_files:
            if container in file_path and 'change' not in file_path:
                try:
                    # Extract date from filename (assuming format includes YYYYMMDD)
                    file_date_str = self._extract_date_from_filename(file_path)
                    if file_date_str:
                        file_date = datetime.datetime.strptime(file_date_str, '%Y%m%d')
                        
                        if file_date.year == year and file_date.month == month:
                            if partial_month:
                                if first_day <= file_date.day <= last_day:
                                    valid_files.append(file_path)
                            else:
                                valid_files.append(file_path)
                                
                except Exception as e:
                    self.logger.warning(f"Could not parse date from filename {file_path}: {e}")
        
        self.logger.info(f"Found {len(valid_files)} matching files")
        return valid_files
    
    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract date string from filename
        
        Args:
            filename: Full file path
        
        Returns:
            Date string in YYYYMMDD format or None
        """
        # Common patterns for date extraction
        import re
        
        # Pattern for YYYYMMDD in filename
        pattern = r'(\d{8})'
        match = re.search(pattern, filename)
        
        if match:
            return match.group(1)
        
        return None
    
    def concatenate_files(
        self,
        file_paths: List[str],
        output_path: str,
        reader_class = None
    ) -> str:
        """
        Concatenate multiple files into a single temporary file
        
        Args:
            file_paths: List of files to concatenate
            output_path: Output file path
            reader_class: Reader class for processing files
        
        Returns:
            Path to concatenated file
        """
        self.logger.info(f"Concatenating {len(file_paths)} files to {output_path}")
        
        try:
            with open(output_path, 'wb') as outfile:
                for i, file_path in enumerate(file_paths):
                    with open(file_path, 'rb') as infile:
                        if i > 0:
                            # Skip header for subsequent files
                            infile.readline()
                        shutil.copyfileobj(infile, outfile)
            
            self.logger.info(f"Successfully concatenated files to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to concatenate files: {str(e)}")
            raise
    
    def validate_file_structure(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate file structure and format
        
        Args:
            file_path: Path to file to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            if os.path.getsize(file_path) == 0:
                return False, "File is empty"
            
            # Try to read first few lines
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline() for _ in range(3)]
            
            if not lines[0]:
                return False, "Cannot read file content"
            
            # Check for common separators
            separators = [';', ',', '\t']
            has_separator = any(sep in lines[0] for sep in separators)
            
            if not has_separator:
                return False, "No recognized column separators found"
            
            return True, "File structure is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        Get file information and statistics
        
        Args:
            file_path: Path to file
        
        Returns:
            Dictionary with file information
        """
        try:
            stat = os.stat(file_path)
            
            return {
                'path': file_path,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': datetime.datetime.fromtimestamp(stat.st_mtime),
                'created_time': datetime.datetime.fromtimestamp(stat.st_ctime),
            }
        except Exception as e:
            self.logger.error(f"Could not get file info for {file_path}: {str(e)}")
            return {}