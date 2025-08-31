"""
SyncTeX Parser Component
Handles reading and parsing of SyncTeX files for precise LaTeX-PDF synchronization.
"""

import gzip
import os
from typing import Dict, List, Optional, Tuple, NamedTuple
from utils import logs_console


class SyncTexRecord(NamedTuple):
    """Represents a single SyncTeX record with precise positioning data."""
    line: int
    column: int
    pdf_page: int
    h_position: float  # Horizontal position in PDF coordinates
    v_position: float  # Vertical position in PDF coordinates
    width: float
    height: float
    tag: str  # Type of element (text, math, etc.)


class SyncTexBox:
    """Represents a SyncTeX box with hierarchical structure."""
    
    def __init__(self, tag: str, page: int, h: float, v: float, w: float, h_val: float, d: float, line: int = 0, col: int = 0):
        self.tag = tag
        self.page = page
        self.h = h  # Horizontal position
        self.v = v  # Vertical position  
        self.w = w  # Width
        self.h_val = h_val  # Height
        self.d = d  # Depth
        self.line = line
        self.column = col
        self.children: List['SyncTexBox'] = []
        self.parent: Optional['SyncTexBox'] = None


class SyncTexParser:
    """
    Parse SyncTeX files for precise LaTeX source to PDF coordinate mapping.
    Provides exact line-to-position synchronization.
    """
    
    def __init__(self):
        """Initialize SyncTeX parser."""
        self.synctex_data: Dict[int, List[SyncTexRecord]] = {}
        self.inverse_map: Dict[Tuple[int, float, float], SyncTexRecord] = {}
        self.boxes: List[SyncTexBox] = []
        self.pages: Dict[int, List[SyncTexBox]] = {}
        self.loaded_file = None
        logs_console.log("SyncTeX Parser initialized", level='INFO')
    
    def parse_synctex_file(self, synctex_path: str) -> bool:
        """
        Parse a SyncTeX file and build coordinate mappings.
        
        Args:
            synctex_path (str): Path to .synctex.gz file
            
        Returns:
            bool: True if parsing successful, False otherwise
        """
        if not os.path.exists(synctex_path):
            logs_console.log(f"SyncTeX file not found: {synctex_path}", level='WARNING')
            return False
            
        try:
            # Clear previous data
            self.synctex_data.clear()
            self.inverse_map.clear()
            self.boxes.clear()
            self.pages.clear()
            
            with gzip.open(synctex_path, 'rt', encoding='utf-8', errors='ignore') as f:
                self._parse_synctex_content(f)
                
            self.loaded_file = synctex_path
            logs_console.log(f"SyncTeX parsed: {len(self.synctex_data)} line mappings, {len(self.boxes)} boxes", level='INFO')
            return True
            
        except Exception as e:
            logs_console.log(f"Error parsing SyncTeX file: {e}", level='ERROR')
            return False
    
    def _parse_synctex_content(self, file_content) -> None:
        """
        Parse the actual SyncTeX file content.
        
        Args:
            file_content: Opened file content
        """
        current_page = 1
        box_stack: List[SyncTexBox] = []
        
        for line_text in file_content:
            line_text = line_text.strip()
            if not line_text:
                continue
                
            # Skip metadata lines
            if line_text.startswith('SyncTeX Version:') or line_text.startswith('Input:') or line_text.startswith('Output:'):
                continue
                
            # Parse different SyncTeX record types
            if line_text.startswith('{'):
                # Page start marker: {page_number
                try:
                    current_page = int(line_text[1:])
                    logs_console.log(f"Starting page {current_page}", level='DEBUG')
                except ValueError:
                    pass
                    
            elif line_text.startswith('}'):
                # Page end marker: }page_number
                try:
                    ended_page = int(line_text[1:])
                    logs_console.log(f"Ending page {ended_page}", level='DEBUG')
                except ValueError:
                    pass
                    
            elif line_text.startswith('['):
                # Box record: [page,line:x,y:width,height,depth
                box = self._parse_box_record(line_text, 'box', current_page)
                if box:
                    if box_stack:
                        box.parent = box_stack[-1]
                        box_stack[-1].children.append(box)
                    box_stack.append(box)
                    self.boxes.append(box)
                    
            elif line_text.startswith('('):
                # Kern/glue record: (page,line:x,y:width,height,depth
                box = self._parse_box_record(line_text, 'kern', current_page)
                if box:
                    if box_stack:
                        box.parent = box_stack[-1]
                        box_stack[-1].children.append(box)
                    else:
                        box_stack.append(box)
                    self.boxes.append(box)
                    
            elif line_text.startswith('h') or line_text.startswith('v'):
                # Position record: hpage,line:x,y:width,height,depth
                box = self._parse_position_record_new(line_text, current_page)
                if box:
                    self.boxes.append(box)
                
        # Build page index
        self._build_page_index()
        self._build_line_mappings()
        logs_console.log(f"SyncTeX parsing complete: {len(self.boxes)} boxes parsed", level='DEBUG')
    
    def _parse_box_record(self, line_text: str, box_type: str, current_page: int = 1) -> Optional[SyncTexBox]:
        """
        Parse SyncTeX box record: [page,line:x,y:width,height,depth or (page,line:x,y:width,height,depth
        
        Args:
            line_text (str): Raw line from SyncTeX file
            box_type (str): Type of box ('box' or 'kern')
            
        Returns:
            Optional[SyncTexBox]: Parsed box or None if parsing fails
        """
        try:
            # Remove opening bracket/parenthesis
            content = line_text[1:]
            
            # Split by colon to separate page,line from coordinates
            parts = content.split(':')
            if len(parts) < 3:
                return None
            
            # Parse page,line
            page_line_parts = parts[0].split(',')
            if len(page_line_parts) < 2:
                return None
                
            # Use current_page from page markers instead of the embedded page number
            # The embedded page number in records is often incorrect or refers to input file
            page = current_page
            line = int(page_line_parts[1])
            
            # Parse x,y coordinates
            coord_parts = parts[1].split(',')
            if len(coord_parts) < 2:
                return None
                
            x = float(coord_parts[0])
            y = float(coord_parts[1])
            
            # Parse width,height,depth
            dim_parts = parts[2].split(',')
            width = float(dim_parts[0]) if len(dim_parts) > 0 and dim_parts[0] else 0.0
            height = float(dim_parts[1]) if len(dim_parts) > 1 and dim_parts[1] else 0.0
            depth = float(dim_parts[2]) if len(dim_parts) > 2 and dim_parts[2] else 0.0
            
            # Convert SyncTeX units to PDF points (1 sp = 1/65536 pt)
            x_pt = x / 65536.0
            y_pt = y / 65536.0
            width_pt = width / 65536.0
            height_pt = height / 65536.0
            depth_pt = depth / 65536.0
            
            return SyncTexBox(box_type, page, x_pt, y_pt, width_pt, height_pt, depth_pt, line, 0)
            
        except (ValueError, IndexError) as e:
            logs_console.log(f"Error parsing {box_type} record '{line_text}': {e}", level='DEBUG')
            return None
    
    def _parse_position_record_new(self, line_text: str, current_page: int = 1) -> Optional[SyncTexBox]:
        """
        Parse position record: hpage,line:x,y:width,height,depth
        
        Args:
            line_text (str): Raw line from SyncTeX file
            
        Returns:
            Optional[SyncTexBox]: Parsed position box or None
        """
        try:
            # Remove h/v prefix
            content = line_text[1:]
            
            # Split by colon
            parts = content.split(':')
            if len(parts) < 2:
                return None
            
            # Parse page,line
            page_line_parts = parts[0].split(',')
            if len(page_line_parts) < 2:
                return None
                
            # Use current_page from page markers instead of the embedded page number
            # The embedded page number in records is often incorrect or refers to input file
            page = current_page
            line = int(page_line_parts[1])
            
            # Parse coordinates and dimensions
            coord_parts = parts[1].split(',')
            if len(coord_parts) < 2:
                return None
                
            x = float(coord_parts[0])
            y = float(coord_parts[1])
            width = float(coord_parts[2]) if len(coord_parts) > 2 and coord_parts[2] else 0.0
            height = float(coord_parts[3]) if len(coord_parts) > 3 and coord_parts[3] else 0.0
            depth = float(coord_parts[4]) if len(coord_parts) > 4 and coord_parts[4] else 0.0
            
            # Convert SyncTeX units to PDF points
            x_pt = x / 65536.0
            y_pt = y / 65536.0
            width_pt = width / 65536.0
            height_pt = height / 65536.0
            depth_pt = depth / 65536.0
            
            position_type = 'h_pos' if line_text.startswith('h') else 'v_pos'
            return SyncTexBox(position_type, page, x_pt, y_pt, width_pt, height_pt, depth_pt, line, 0)
            
        except (ValueError, IndexError) as e:
            logs_console.log(f"Error parsing position record '{line_text}': {e}", level='DEBUG')
            return None

    def _parse_page_record(self, line: str) -> int:
        """Parse page number from SyncTeX record."""
        try:
            return int(line[1:line.find(':')])
        except (ValueError, IndexError):
            return 1
    
    def _parse_open_box(self, line: str, page: int) -> Optional[SyncTexBox]:
        """Parse opening box record."""
        try:
            # Format: (tag:line,col:h,v:w,h,d
            parts = line[1:].split(':')
            if len(parts) < 4:
                return None
                
            tag = parts[0]
            line_col = parts[1].split(',')
            line_num = int(line_col[0]) if line_col[0] else 0
            col_num = int(line_col[1]) if len(line_col) > 1 and line_col[1] else 0
            
            pos_parts = parts[2].split(',')
            h = float(pos_parts[0]) if pos_parts[0] else 0.0
            v = float(pos_parts[1]) if len(pos_parts) > 1 and pos_parts[1] else 0.0
            
            dim_parts = parts[3].split(',')
            w = float(dim_parts[0]) if dim_parts[0] else 0.0
            h_val = float(dim_parts[1]) if len(dim_parts) > 1 and dim_parts[1] else 0.0
            d = float(dim_parts[2]) if len(dim_parts) > 2 and dim_parts[2] else 0.0
            
            return SyncTexBox(tag, page, h, v, w, h_val, d, line_num, col_num)
            
        except (ValueError, IndexError) as e:
            logs_console.log(f"Error parsing box record '{line}': {e}", level='DEBUG')
            return None
    
    def _parse_position_record(self, line: str, page: int, box_stack: List[SyncTexBox]) -> None:
        """Parse position record and associate with current box."""
        if not box_stack:
            return
            
        try:
            current_box = box_stack[-1]
            # Position records can update the current box position
            if line.startswith('h'):
                current_box.h = float(line[1:])
            elif line.startswith('v'):
                current_box.v = float(line[1:])
        except (ValueError, IndexError):
            pass
    
    def _build_page_index(self) -> None:
        """Build page-based index of boxes."""
        for box in self.boxes:
            if box.page not in self.pages:
                self.pages[box.page] = []
            self.pages[box.page].append(box)
    
    def _build_line_mappings(self) -> None:
        """Build line-to-coordinate mappings from parsed boxes."""
        for box in self.boxes:
            if box.line > 0:
                record = SyncTexRecord(
                    line=box.line,
                    column=box.column,
                    pdf_page=box.page,
                    h_position=box.h,
                    v_position=box.v,
                    width=box.w,
                    height=box.h_val,
                    tag=box.tag
                )
                
                # Add to line-based mapping
                if box.line not in self.synctex_data:
                    self.synctex_data[box.line] = []
                self.synctex_data[box.line].append(record)
                
                # Add to position-based inverse mapping
                pos_key = (box.page, round(box.h, 2), round(box.v, 2))
                self.inverse_map[pos_key] = record
    
    def get_pdf_position(self, line_number: int) -> Optional[SyncTexRecord]:
        """
        Get precise PDF position for a source line number.
        
        Args:
            line_number (int): Line number in LaTeX source
            
        Returns:
            Optional[SyncTexRecord]: PDF position data or None if not found
        """
        if line_number in self.synctex_data:
            # Return the first (most relevant) record for this line
            records = self.synctex_data[line_number]
            if records:
                return records[0]
        
        # Find closest line if exact match not found
        closest_line = self._find_closest_line(line_number)
        if closest_line and closest_line in self.synctex_data:
            return self.synctex_data[closest_line][0]
            
        return None
    
    def get_source_position(self, pdf_page: int, h_pos: float, v_pos: float) -> Optional[SyncTexRecord]:
        """
        Get source line for PDF coordinates (inverse search).
        
        Args:
            pdf_page (int): PDF page number
            h_pos (float): Horizontal position
            v_pos (float): Vertical position
            
        Returns:
            Optional[SyncTexRecord]: Source position data or None if not found
        """
        # Try exact match first
        pos_key = (pdf_page, round(h_pos, 2), round(v_pos, 2))
        if pos_key in self.inverse_map:
            return self.inverse_map[pos_key]
        
        # Find closest position
        if pdf_page in self.pages:
            closest_box = self._find_closest_box(self.pages[pdf_page], h_pos, v_pos)
            if closest_box and closest_box.line > 0:
                return SyncTexRecord(
                    line=closest_box.line,
                    column=closest_box.column,
                    pdf_page=closest_box.page,
                    h_position=closest_box.h,
                    v_position=closest_box.v,
                    width=closest_box.w,
                    height=closest_box.h_val,
                    tag=closest_box.tag
                )
        
        return None
    
    def _find_closest_line(self, target_line: int) -> Optional[int]:
        """Find the closest line number with SyncTeX data."""
        available_lines = sorted(self.synctex_data.keys())
        if not available_lines:
            return None
        
        # Binary search for closest line
        left, right = 0, len(available_lines) - 1
        closest = available_lines[0]
        min_diff = abs(available_lines[0] - target_line)
        
        while left <= right:
            mid = (left + right) // 2
            diff = abs(available_lines[mid] - target_line)
            
            if diff < min_diff:
                min_diff = diff
                closest = available_lines[mid]
            
            if available_lines[mid] < target_line:
                left = mid + 1
            else:
                right = mid - 1
                
        return closest
    
    def _find_closest_box(self, boxes: List[SyncTexBox], h_pos: float, v_pos: float) -> Optional[SyncTexBox]:
        """Find the closest box to given PDF coordinates."""
        if not boxes:
            return None
        
        closest_box = None
        min_distance = float('inf')
        
        for box in boxes:
            if box.line > 0:  # Only consider boxes with line information
                distance = ((box.h - h_pos) ** 2 + (box.v - v_pos) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    closest_box = box
        
        return closest_box
    
    def has_synctex_data(self) -> bool:
        """Check if SyncTeX data is available."""
        return len(self.synctex_data) > 0
    
    def get_line_range(self) -> Tuple[int, int]:
        """Get the range of line numbers with SyncTeX data."""
        if not self.synctex_data:
            return (0, 0)
        lines = list(self.synctex_data.keys())
        return (min(lines), max(lines))
    
    def get_page_count(self) -> int:
        """Get the number of pages in the SyncTeX data."""
        return len(self.pages)