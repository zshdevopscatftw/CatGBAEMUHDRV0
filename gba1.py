#!/usr/bin/env python3
"""
catgbaemuhdrv0.py - Ultra-Enhanced GBA Emulator with libmeow0.1 Core
Wholesome Pwny Council Certified 🐱🍓💕
License: Hugware v2.0 - Free to use with snuggles and strawberry milk
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
import struct
import array
import time
import threading
import collections
import zlib
import json
import os
import sys
import math
from typing import Dict, List, Tuple, Optional, Any, Callable
import queue

# ======================
# LIBMEOW0.1 CORE SYSTEM
# ======================

class LibmeowLoader:
    """ROM detection and system switching - pure vibes ✨"""
    
    SYSTEMS = {
        'GBA': 'Game Boy Advance',
        'GBC': 'Game Boy Color', 
        'GB': 'Game Boy',
        'UNKNOWN': 'Unknown ROM'
    }
    
    @staticmethod
    def sniff_rom(rom_data):
        """Sniff out the ROM type like a cute kitty~"""
        if len(rom_data) < 0x150:
            return 'UNKNOWN'
        
        # GBA detection
        if rom_data[0xB2] == 0x96:
            return 'GBA'
        
        # GB/GBC detection
        nintendo_logo = rom_data[0x104:0x134]
        logo_sum = sum(nintendo_logo)
        if 0x14FA <= logo_sum <= 0x1546:
            return 'GBC' if rom_data[0x143] == 0x80 else 'GB'
        
        return 'UNKNOWN'
    
    def __init__(self):
        self.current_core = None
        self.rom_type = None
        self.rom_data = None
        print("[libmeow0.1] System initialized with snuggles~ 🐱💕")
    
    def load(self, rom_path):
        """Load and detect ROM"""
        with open(rom_path, 'rb') as f:
            self.rom_data = f.read()
        self.rom_type = self.sniff_rom(self.rom_data)
        print(f"[libmeow0.1] Detected: {self.SYSTEMS.get(self.rom_type)}")
        return self.rom_type

class LibmeowCheat:
    """Cutesy but deadly cheat engine 🎀🔥"""
    
    def __init__(self):
        self.active_codes = []
        self.cheat_file = "kitty_cheats.txt"
        self.master_enable = True
        self.code_types = {
            'raw': 'Raw Memory',
            'gameshark': 'GameShark',
            'actionreplay': 'Action Replay',
            'codebreaker': 'CodeBreaker'
        }
    
    def apply_cheat(self, address, value, code_type="raw", description="Nyaa~ Cheat"):
        """Apply a cheat with sparkles ✨"""
        cheat = {
            'addr': address & 0xFFFFFFFF,
            'value': value & 0xFF,
            'type': code_type,
            'enabled': True,
            'description': description
        }
        self.active_codes.append(cheat)
        print(f"[libmeow0.1] Applied {code_type} cheat: 0x{address:08X}=0x{value:02X}")
        return len(self.active_codes) - 1
    
    def parse_code(self, code_str):
        """Parse multiple cheat code formats"""
        code = code_str.strip().replace(' ', '').upper()
        
        # Raw: 02000000:FF
        if ':' in code:
            addr_str, val_str = code.split(':')
            try:
                addr = int(addr_str, 16)
                val = int(val_str, 16)
                return self.apply_cheat(addr, val, "raw", f"Raw: {code}")
            except:
                pass
        
        # GameShark style
        if len(code) == 16:
            try:
                addr = int(code[2:10], 16)
                val = int(code[10:], 16)
                return self.apply_cheat(addr, val, "gameshark", f"GS: {code}")
            except:
                pass
        
        return None
    
    def toggle_cheat(self, index, enabled=True):
        """Enable/disable specific cheat"""
        if 0 <= index < len(self.active_codes):
            self.active_codes[index]['enabled'] = enabled
    
    def save_to_file(self, filename=None):
        """Save cheats to file"""
        if filename is None:
            filename = self.cheat_file
        with open(filename, 'w') as f:
            for cheat in self.active_codes:
                f.write(f"{cheat['type']}:0x{cheat['addr']:08X}:0x{cheat['value']:02X}:{cheat['description']}\n")
    
    def load_from_file(self, filename=None):
        """Load cheats from file"""
        if filename is None:
            filename = self.cheat_file
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for line in f:
                    self.parse_code(line.strip())

class LibmeowFilter:
    """Post-processing filters for extra cuteness 🌈"""
    
    FILTERS = {
        'none': 'No Filter',
        'scanlines': 'CRT Scanlines',
        'pixelate': 'Pixelate 2x',
        'crt_glow': 'CRT Glow',
        'tv_mode': 'TV Mode',
        'bilinear': 'Bilinear',
        'hq2x': 'HQ2X (Simulated)'
    }
    
    def __init__(self):
        self.current_filter = "none"
        self.filter_intensity = 1.0
        self.scanline_opacity = 0.3
    
    def apply_filter(self, frame_data, width=240, height=160):
        """Apply the selected filter to frame buffer"""
        if self.current_filter == "none":
            return frame_data
        
        # Convert to list for manipulation
        pixels = list(frame_data)
        
        if self.current_filter == "scanlines":
            return self._apply_scanlines(pixels, width, height)
        elif self.current_filter == "pixelate":
            return self._apply_pixelate(pixels, width, height, 2)
        elif self.current_filter == "crt_glow":
            return self._apply_crt_glow(pixels, width, height)
        elif self.current_filter == "tv_mode":
            return self._apply_tv_mode(pixels, width, height)
        elif self.current_filter == "bilinear":
            return self._apply_bilinear(pixels, width, height)
        elif self.current_filter == "hq2x":
            return self._apply_hq2x(pixels, width, height)
        
        return bytes(pixels)
    
    def _apply_scanlines(self, pixels, width, height):
        """Add CRT scanlines"""
        result = pixels[:]
        for y in range(height):
            if y % 2 == 0:
                line_start = y * width * 3
                for x in range(width):
                    idx = line_start + x * 3
                    # Darken scanline
                    result[idx] = int(pixels[idx] * (1.0 - self.scanline_opacity))
                    result[idx + 1] = int(pixels[idx + 1] * (1.0 - self.scanline_opacity))
                    result[idx + 2] = int(pixels[idx + 2] * (1.0 - self.scanline_opacity))
        return bytes(result)
    
    def _apply_pixelate(self, pixels, width, height, scale):
        """Pixelate effect"""
        result = pixels[:]
        for y in range(0, height, scale):
            for x in range(0, width, scale):
                # Average color in block
                r_sum, g_sum, b_sum = 0, 0, 0
                count = 0
                
                for dy in range(scale):
                    for dx in range(scale):
                        yy, xx = y + dy, x + dx
                        if yy < height and xx < width:
                            idx = (yy * width + xx) * 3
                            r_sum += pixels[idx]
                            g_sum += pixels[idx + 1]
                            b_sum += pixels[idx + 2]
                            count += 1
                
                if count > 0:
                    avg_r = r_sum // count
                    avg_g = g_sum // count
                    avg_b = b_sum // count
                    
                    # Apply to block
                    for dy in range(scale):
                        for dx in range(scale):
                            yy, xx = y + dy, x + dx
                            if yy < height and xx < width:
                                idx = (yy * width + xx) * 3
                                result[idx] = avg_r
                                result[idx + 1] = avg_g
                                result[idx + 2] = avg_b
        
        return bytes(result)
    
    def _apply_crt_glow(self, pixels, width, height):
        """Simple CRT glow effect"""
        result = pixels[:]
        for y in range(height):
            for x in range(width):
                idx = (y * width + x) * 3
                
                # Add slight glow by blending with neighbors
                if x > 0 and x < width - 1 and y > 0 and y < height - 1:
                    r, g, b = pixels[idx], pixels[idx + 1], pixels[idx + 2]
                    
                    # Sample neighbors
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            n_idx = ((y + dy) * width + (x + dx)) * 3
                            r += pixels[n_idx] // 16
                            g += pixels[n_idx + 1] // 16
                            b += pixels[n_idx + 2] // 16
                    
                    result[idx] = min(255, r)
                    result[idx + 1] = min(255, g)
                    result[idx + 2] = min(255, b)
        
        return bytes(result)
    
    def _apply_tv_mode(self, pixels, width, height):
        """TV/VHS style effect"""
        result = pixels[:]
        for y in range(height):
            # Add horizontal blur
            for x in range(1, width - 1):
                idx = (y * width + x) * 3
                
                # Simple horizontal blur
                left_idx = idx - 3
                right_idx = idx + 3
                
                r = (pixels[left_idx] + pixels[idx] * 2 + pixels[right_idx]) // 4
                g = (pixels[left_idx + 1] + pixels[idx + 1] * 2 + pixels[right_idx + 1]) // 4
                b = (pixels[left_idx + 2] + pixels[idx + 2] * 2 + pixels[right_idx + 2]) // 4
                
                # Add slight color bleed
                r = min(255, int(r * 1.1))
                b = min(255, int(b * 1.05))
                
                result[idx] = r
                result[idx + 1] = g
                result[idx + 2] = b
        
        return bytes(result)
    
    def _apply_bilinear(self, pixels, width, height):
        """Bilinear interpolation for smoother scaling"""
        # This is a simplified version for demonstration
        result = pixels[:]
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                idx = (y * width + x) * 3
                
                # Get neighbors
                top = (y - 1) * width + x
                bottom = (y + 1) * width + x
                left = y * width + (x - 1)
                right = y * width + (x + 1)
                
                # Average with neighbors
                r = (pixels[top * 3] + pixels[bottom * 3] + 
                     pixels[left * 3] + pixels[right * 3] + 
                     pixels[idx] * 2) // 6
                g = (pixels[top * 3 + 1] + pixels[bottom * 3 + 1] + 
                     pixels[left * 3 + 1] + pixels[right * 3 + 1] + 
                     pixels[idx + 1] * 2) // 6
                b = (pixels[top * 3 + 2] + pixels[bottom * 3 + 2] + 
                     pixels[left * 3 + 2] + pixels[right * 3 + 2] + 
                     pixels[idx + 2] * 2) // 6
                
                result[idx] = r
                result[idx + 1] = g
                result[idx + 2] = b
        
        return bytes(result)
    
    def _apply_hq2x(self, pixels, width, height):
        """Simplified HQ2X-like filter"""
        result = pixels[:]
        # This would normally be complex; simplified version
        for y in range(height):
            for x in range(width):
                idx = (y * width + x) * 3
                
                # Simple edge detection and sharpening
                if x > 0 and x < width - 1 and y > 0 and y < height - 1:
                    # Check for edges
                    current = pixels[idx] + pixels[idx + 1] + pixels[idx + 2]
                    left = pixels[idx - 3] + pixels[idx - 2] + pixels[idx - 1]
                    right = pixels[idx + 3] + pixels[idx + 4] + pixels[idx + 5]
                    
                    if abs(current - left) > 30 or abs(current - right) > 30:
                        # Edge - sharpen
                        result[idx] = min(255, pixels[idx] * 6 // 5)
                        result[idx + 1] = min(255, pixels[idx + 1] * 6 // 5)
                        result[idx + 2] = min(255, pixels[idx + 2] * 6 // 5)
        
        return bytes(result)

class LibmeowDebug:
    """Debugger for when things get messy 🐛🔍"""
    
    def __init__(self, parent):
        self.parent = parent
        self.breakpoints = set()
        self.watchpoints = {}
        self.log_file = "meow_debug.log"
        self.history = []
        self.paused = False
        self.step_mode = False
    
    def add_breakpoint(self, address, condition=None):
        """Set a breakpoint at address"""
        bp_id = len(self.breakpoints) + 1
        self.breakpoints.add((address, condition, bp_id))
        print(f"[libmeow0.1] Breakpoint set at 0x{address:08X} (#{bp_id})")
        return bp_id
    
    def remove_breakpoint(self, bp_id):
        """Remove breakpoint by ID"""
        self.breakpoints = {bp for bp in self.breakpoints if bp[2] != bp_id}
    
    def cpu_step(self):
        """Single step the CPU for debugging"""
        if self.parent.cpu:
            self.step_mode = True
            self.paused = False
    
    def pause(self):
        """Pause emulation"""
        self.paused = True
        print("[libmeow0.1] Emulation paused")
    
    def resume(self):
        """Resume emulation"""
        self.paused = False
        self.step_mode = False
        print("[libmeow0.1] Emulation resumed")
    
    def log(self, message):
        """Log debug message"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.history.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.history) > 1000:
            self.history.pop(0)
        
        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
        
        return log_entry
    
    def get_cpu_state(self):
        """Get current CPU state for display"""
        if not self.parent.cpu:
            return {}
        
        return {
            'pc': f"0x{self.parent.cpu.pc:08X}",
            'registers': [f"0x{r:08X}" for r in self.parent.cpu.registers] if hasattr(self.parent.cpu, 'registers') else [],
            'flags': self.parent.cpu.flags if hasattr(self.parent.cpu, 'flags') else {},
            'cycles': self.parent.cycles if hasattr(self.parent, 'cycles') else 0
        }
    
    def read_memory(self, address, size=256):
        """Read memory region for debug view"""
        if not self.parent.mmu:
            return b'\x00' * size
        
        data = bytearray()
        for i in range(size):
            try:
                data.append(self.parent.mmu.read_byte(address + i))
            except:
                data.append(0)
        return bytes(data)

class LibmeowState:
    """Save state and rewind system 💾⏪"""
    
    def __init__(self):
        self.states = {}
        self.state_slots = 10  # 0-9
        self.rewind_buffer = collections.deque(maxlen=60)  # ~2 seconds at 30fps
        self.auto_save = False
        self.auto_save_interval = 300  # 5 minutes
    
    def save_state(self, slot, emulator_state):
        """Save state to slot"""
        compressed = zlib.compress(json.dumps(emulator_state).encode())
        self.states[slot] = {
            'data': compressed,
            'timestamp': time.time(),
            'slot': slot
        }
        
        # Add to rewind buffer
        self.rewind_buffer.appendleft(compressed)
        
        print(f"[libmeow0.1] State saved to slot {slot}")
        return True
    
    def load_state(self, slot):
        """Load state from slot"""
        if slot in self.states:
            state_data = self.states[slot]['data']
            try:
                return json.loads(zlib.decompress(state_data))
            except:
                pass
        return None
    
    def rewind(self, frames=1):
        """Rewind specified number of frames"""
        if len(self.rewind_buffer) >= frames:
            # Skip current state
            for _ in range(frames - 1):
                if self.rewind_buffer:
                    self.rewind_buffer.popleft()
            
            if self.rewind_buffer:
                state_data = self.rewind_buffer.popleft()
                try:
                    return json.loads(zlib.decompress(state_data))
                except:
                    pass
        return None
    
    def save_to_file(self, filename):
        """Save all states to file"""
        state_package = {
            'states': {k: v['data'].hex() for k, v in self.states.items()},
            'rewind_buffer': [data.hex() for data in self.rewind_buffer],
            'timestamp': time.time()
        }
        with open(filename, 'w') as f:
            json.dump(state_package, f)
    
    def load_from_file(self, filename):
        """Load states from file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                state_package = json.load(f)
            
            self.states = {}
            for slot, hex_data in state_package['states'].items():
                self.states[int(slot)] = {
                    'data': bytes.fromhex(hex_data),
                    'timestamp': state_package['timestamp'],
                    'slot': int(slot)
                }
            
            self.rewind_buffer = collections.deque(
                [bytes.fromhex(hex_data) for hex_data in state_package['rewind_buffer']],
                maxlen=60
            )

class LibmeowJoy:
    """Gamepad/joystick support 🎮"""
    
    # GBA button mapping
    GBA_BUTTONS = {
        'A': 0,
        'B': 1,
        'SELECT': 2,
        'START': 3,
        'RIGHT': 4,
        'LEFT': 5,
        'UP': 6,
        'DOWN': 7,
        'R': 8,
        'L': 9
    }
    
    def __init__(self):
        self.joystick = None
        self.keyboard_map = {
            'z': 'A', 'x': 'B', 'enter': 'START', 'shift': 'SELECT',
            'up': 'UP', 'down': 'DOWN', 'left': 'LEFT', 'right': 'RIGHT',
            'a': 'L', 's': 'R'
        }
        self.gamepad_map = {}
        self.autofire = {'A': False, 'B': False}
        self.autofire_rate = 10  # Hz
        
        print("[libmeow0.1] Input system ready~ 🎮")
    
    def map_keyboard(self, key, button):
        """Map keyboard key to GBA button"""
        self.keyboard_map[key.lower()] = button
        print(f"[libmeow0.1] Mapped {key} -> {button}")
    
    def set_autofire(self, button, enabled=True):
        """Enable/disable autofire for button"""
        if button in self.autofire:
            self.autofire[button] = enabled
            print(f"[libmeow0.1] Autofire for {button}: {'ON' if enabled else 'OFF'}")
    
    def process_keyboard(self, keys_pressed):
        """Convert keyboard state to GBA button state"""
        button_state = 0
        
        for key, button in self.keyboard_map.items():
            if key in keys_pressed and keys_pressed[key]:
                if button in self.GBA_BUTTONS:
                    button_state |= 1 << self.GBA_BUTTONS[button]
        
        # Apply autofire
        current_time = time.time()
        if hasattr(self, 'last_autofire'):
            if (current_time - self.last_autofire) > (1.0 / self.autofire_rate):
                for button, enabled in self.autofire.items():
                    if enabled and button in self.GBA_BUTTONS:
                        button_state ^= 1 << self.GBA_BUTTONS[button]  # Toggle
                self.last_autofire = current_time
        else:
            self.last_autofire = current_time
        
        return button_state & 0x3FF  # 10 buttons max

class LibmeowAudio:
    """Audio system with filters 🎵"""
    
    def __init__(self):
        self.enabled = True
        self.volume = 0.8
        self.muted = False
        self.sample_rate = 44100
        self.buffer_size = 2048
        self.audio_filters = {
            'lowpass': True,
            'echo': False,
            'reverb': False
        }
        
        print("[libmeow0.1] Audio system initialized~ 🎧")
    
    def process_audio(self, samples):
        """Process audio samples with filters"""
        if not self.enabled or self.muted:
            return [0] * len(samples)
        
        # Apply volume
        samples = [s * self.volume for s in samples]
        
        # Apply filters (simplified)
        if self.audio_filters['lowpass']:
            samples = self._apply_lowpass(samples)
        
        if self.audio_filters['echo']:
            samples = self._apply_echo(samples)
        
        return samples
    
    def _apply_lowpass(self, samples):
        """Simple low-pass filter"""
        result = [0] * len(samples)
        alpha = 0.3
        
        result[0] = samples[0]
        for i in range(1, len(samples)):
            result[i] = alpha * samples[i] + (1 - alpha) * result[i-1]
        
        return result
    
    def _apply_echo(self, samples):
        """Simple echo effect"""
        result = samples[:]
        delay = 2205  # 0.05 seconds at 44100 Hz
        decay = 0.3
        
        for i in range(delay, len(samples)):
            result[i] += samples[i - delay] * decay
        
        return result

# ======================
# EMULATOR CORE CLASSES
# ======================

class ARM7TDMI:
    """ARM7TDMI CPU Core (Simplified)"""
    
    def __init__(self):
        self.registers = [0] * 16  # R0-R15
        self.pc = 0x08000000  # GBA ROM entry point
        self.cpsr = 0
        self.memory = None
        self.running = False
        self.cycles = 0
        
        print("[CPU] ARM7TDMI initialized")
    
    def execute(self):
        """Execute one instruction (simplified)"""
        if not self.memory or not self.running:
            return 0
        
        try:
            # Fetch instruction (simplified)
            instr = self.memory.read_word(self.pc)
            
            # Decode and execute (simplified MOV instruction)
            if (instr & 0x0FF00000) == 0x03A00000:  # MOV immediate
                rd = (instr >> 12) & 0xF
                imm = instr & 0xFF
                rot = ((instr >> 8) & 0xF) * 2
                imm = (imm >> rot) | (imm << (32 - rot))
                self.registers[rd] = imm
            
            self.pc += 4
            self.cycles += 1
            
            return 1  # Cycle count
        except:
            self.pc += 4
            return 1
    
    def reset(self):
        """Reset CPU"""
        self.registers = [0] * 16
        self.pc = 0x08000000
        self.cpsr = 0
        self.cycles = 0

class MMU:
    """Memory Management Unit"""
    
    def __init__(self):
        self.ram = bytearray(0x40000)  # 256KB WRAM
        self.vram = bytearray(0x18000)  # 96KB VRAM
        self.rom = bytearray()
        self.bios = bytearray(0x4000)   # 16KB BIOS
        
        print("[MMU] Memory system initialized")
    
    def read_byte(self, address):
        """Read byte from memory"""
        address &= 0xFFFFFFFF
        
        if address < 0x4000:
            return self.bios[address] if address < len(self.bios) else 0
        elif 0x02000000 <= address < 0x02040000:
            return self.ram[address - 0x02000000]
        elif 0x06000000 <= address < 0x06018000:
            return self.vram[address - 0x06000000]
        elif 0x08000000 <= address < 0x08000000 + len(self.rom):
            return self.rom[address - 0x08000000]
        
        return 0
    
    def read_word(self, address):
        """Read 32-bit word"""
        address &= 0xFFFFFFFC
        b0 = self.read_byte(address)
        b1 = self.read_byte(address + 1)
        b2 = self.read_byte(address + 2)
        b3 = self.read_byte(address + 3)
        return (b3 << 24) | (b2 << 16) | (b1 << 8) | b0
    
    def write_byte(self, address, value):
        """Write byte to memory"""
        address &= 0xFFFFFFFF
        value &= 0xFF
        
        if 0x02000000 <= address < 0x02040000:
            self.ram[address - 0x02000000] = value
        elif 0x06000000 <= address < 0x06018000:
            self.vram[address - 0x06000000] = value
    
    def load_rom(self, rom_data):
        """Load ROM into memory"""
        self.rom = bytearray(rom_data)
        print(f"[MMU] ROM loaded: {len(rom_data)} bytes")

class PPU:
    """Picture Processing Unit"""
    
    def __init__(self):
        self.width = 240
        self.height = 160
        self.framebuffer = bytearray(self.width * self.height * 3)
        self.mode = 3  # Bitmap mode
        self.vblank = False
        self.frame_count = 0
        
        print("[PPU] Graphics system initialized")
    
    def render_frame(self, vram):
        """Render a frame from VRAM (simplified)"""
        # Simple bitmap mode 3 renderer
        for y in range(self.height):
            for x in range(self.width):
                # Calculate VRAM offset
                offset = (y * self.width + x) * 2
                if offset + 1 < len(vram):
                    # 16-bit color: BBBBBGGG GGGRRRRR
                    color16 = (vram[offset + 1] << 8) | vram[offset]
                    
                    # Convert to RGB888
                    r = ((color16 >> 0) & 0x1F) << 3
                    g = ((color16 >> 5) & 0x1F) << 3
                    b = ((color16 >> 10) & 0x1F) << 3
                    
                    # Store in framebuffer
                    idx = (y * self.width + x) * 3
                    self.framebuffer[idx] = r
                    self.framebuffer[idx + 1] = g
                    self.framebuffer[idx + 2] = b
        
        self.frame_count += 1
        return self.framebuffer
    
    def get_fps(self):
        """Calculate FPS"""
        if hasattr(self, 'last_time'):
            current_time = time.time()
            fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time
            return fps
        else:
            self.last_time = time.time()
            return 0

# ======================
# MAIN EMULATOR CLASS
# ======================

class CatEMU:
    """Main emulator class with libmeow0.1 integration"""
    
    def __init__(self):
        print("[CatEMU] Initializing with libmeow0.1 magic~ ✨")
        
        # Core components
        self.cpu = ARM7TDMI()
        self.mmu = MMU()
        self.ppu = PPU()
        
        # libmeow0.1 modules
        self.libmeow = LibmeowLoader()
        self.cheats = LibmeowCheat()
        self.debugger = LibmeowDebug(self)
        self.filters = LibmeowFilter()
        self.state_manager = LibmeowState()
        self.joypad = LibmeowJoy()
        self.audio = LibmeowAudio()
        
        # Emulator state
        self.running = False
        self.paused = False
        self.speed = 1.0
        self.frame_skip = 0
        self.keys_pressed = {}
        self.rom_path = None
        self.current_frame = None
        
        # Performance tracking
        self.frame_time = 0
        self.last_frame = time.time()
        
        print("[CatEMU] Ready to play! 🎮")
    
    def load_rom(self, rom_path):
        """Load ROM file"""
        try:
            self.rom_path = rom_path
            rom_type = self.libmeow.load(rom_path)
            
            with open(rom_path, 'rb') as f:
                rom_data = f.read()
            
            self.mmu.load_rom(rom_data)
            self.cpu.memory = self.mmu
            self.cpu.reset()
            
            # Enable cheat system
            self._enable_cheat_system()
            
            print(f"[CatEMU] ROM loaded successfully: {os.path.basename(rom_path)}")
            return True
        except Exception as e:
            print(f"[CatEMU] Error loading ROM: {e}")
            return False
    
    def _enable_cheat_system(self):
        """Inject cheat system into memory reads"""
        original_read = self.mmu.read_byte
        
        def cheat_aware_read(address):
            # Check active cheats first
            for cheat in self.cheats.active_codes:
                if cheat['enabled'] and cheat['addr'] == address:
                    return cheat['value']
            return original_read(address)
        
        self.mmu.read_byte = cheat_aware_read
    
    def run_frame(self):
        """Run one frame of emulation"""
        if not self.running or self.paused:
            return None
        
        if self.debugger.paused and not self.debugger.step_mode:
            return self.current_frame
        
        start_time = time.time()
        
        # Run CPU for one frame (simplified)
        cycles_target = 280896  # GBA cycles per frame at 16.78MHz
        
        while self.cpu.cycles < cycles_target:
            self.cpu.execute()
            
            # Check for breakpoints
            if (self.cpu.pc, None, 0) in self.debugger.breakpoints:
                self.debugger.pause()
                self.debugger.log(f"Breakpoint hit at 0x{self.cpu.pc:08X}")
                break
        
        # Reset cycle counter for next frame
        self.cpu.cycles = 0
        
        # Render frame
        framebuffer = self.ppu.render_frame(self.mmu.vram)
        
        # Apply graphics filter
        if self.filters.current_filter != "none":
            framebuffer = self.filters.apply_filter(framebuffer)
        
        self.current_frame = framebuffer
        
        # Auto-save state
        if self.state_manager.auto_save:
            if time.time() - getattr(self, 'last_auto_save', 0) > self.state_manager.auto_save_interval:
                state = self._get_state()
                self.state_manager.save_state('auto', state)
                self.last_auto_save = time.time()
        
        # Calculate frame time
        self.frame_time = time.time() - start_time
        
        # Frame skipping
        if self.frame_skip > 0:
            if random.random() < (self.frame_skip / 10.0):
                return None
        
        return framebuffer
    
    def _get_state(self):
        """Get current emulator state for saving"""
        return {
            'cpu': {
                'registers': self.cpu.registers[:],
                'pc': self.cpu.pc,
                'cpsr': self.cpu.cpsr,
                'cycles': self.cpu.cycles
            },
            'mmu': {
                'ram': list(self.mmu.ram),
                'vram': list(self.mmu.vram)
            },
            'timestamp': time.time()
        }
    
    def _set_state(self, state):
        """Restore emulator state"""
        if 'cpu' in state:
            self.cpu.registers = state['cpu']['registers'][:]
            self.cpu.pc = state['cpu']['pc']
            self.cpu.cpsr = state['cpu']['cpsr']
            self.cpu.cycles = state['cpu']['cycles']
        
        if 'mmu' in state:
            self.mmu.ram = bytearray(state['mmu']['ram'])
            self.mmu.vram = bytearray(state['mmu']['vram'])
    
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        if self.paused:
            self.debugger.pause()
        else:
            self.debugger.resume()
    
    def set_speed(self, speed):
        """Set emulation speed multiplier"""
        self.speed = max(0.1, min(10.0, speed))
    
    def save_state(self, slot=0):
        """Save state to slot"""
        state = self._get_state()
        return self.state_manager.save_state(slot, state)
    
    def load_state(self, slot=0):
        """Load state from slot"""
        state = self.state_manager.load_state(slot)
        if state:
            self._set_state(state)
            return True
        return False
    
    def rewind(self, frames=1):
        """Rewind emulation"""
        state = self.state_manager.rewind(frames)
        if state:
            self._set_state(state)
            return True
        return False
    
    def key_down(self, key):
        """Handle key press"""
        self.keys_pressed[key] = True
    
    def key_up(self, key):
        """Handle key release"""
        self.keys_pressed[key] = False

# ======================
# GUI INTERFACE
# ======================

class CatEMUGUI:
    """Main GUI for the emulator"""
    
    def __init__(self):
        self.emu = CatEMU()
        self.root = tk.Tk()
        self.root.title("CatGBAEmuHDRV0 - libmeow0.1 🐱✨")
        self.root.geometry("800x600")
        
        # Variables
        self.rom_loaded = False
        self.emulation_thread = None
        self.running = False
        self.current_filter = tk.StringVar(value="none")
        self.speed_var = tk.DoubleVar(value=1.0)
        self.frame_skip_var = tk.IntVar(value=0)
        
        # Setup GUI
        self.setup_menu()
        self.setup_main_frame()
        self.setup_side_panel()
        self.setup_status_bar()
        
        # Bind keys
        self.setup_key_bindings()
        
        # Start update loop
        self.update_interval = 16  # ~60 FPS
        self.root.after(self.update_interval, self.update)
    
    def setup_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open ROM 🎮", command=self.open_rom, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save State 💾", command=lambda: self.save_state_dialog())
        file_menu.add_command(label="Load State 📂", command=lambda: self.load_state_dialog())
        file_menu.add_separator()
        file_menu.add_command(label="Exit 🚪", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Emulation menu
        emu_menu = tk.Menu(menubar, tearoff=0)
        emu_menu.add_command(label="Play/Pause ⏯️", command=self.toggle_play_pause, accelerator="Space")
        emu_menu.add_command(label="Reset 🔄", command=self.reset_emu)
        emu_menu.add_command(label="Rewind ⏪", command=lambda: self.emu.rewind(10))
        emu_menu.add_separator()
        
        # Speed submenu
        speed_menu = tk.Menu(emu_menu, tearoff=0)
        for speed in [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
            speed_menu.add_radiobutton(label=f"{speed}x", variable=self.speed_var, 
                                      value=speed, command=self.update_speed)
        emu_menu.add_cascade(label="Speed", menu=speed_menu)
        menubar.add_cascade(label="Emulation", menu=emu_menu)
        
        # Cheats menu
        cheat_menu = tk.Menu(menubar, tearoff=0)
        cheat_menu.add_command(label="Cheat Editor 🎮", command=self.open_cheat_editor)
        cheat_menu.add_command(label="Load Cheats 📂", command=lambda: self.emu.cheats.load_from_file())
        cheat_menu.add_command(label="Save Cheats 💾", command=lambda: self.emo.cheats.save_to_file())
        menubar.add_cascade(label="Cheats", menu=cheat_menu)
        
        # Graphics menu
        gfx_menu = tk.Menu(menubar, tearoff=0)
        for filter_name, display_name in LibmeowFilter.FILTERS.items():
            gfx_menu.add_radiobutton(label=display_name, variable=self.current_filter,
                                    value=filter_name, command=self.change_filter)
        
        gfx_menu.add_separator()
        gfx_menu.add_checkbutton(label="Auto Frameskip", 
                                command=lambda: self.toggle_frameskip())
        menubar.add_cascade(label="Graphics", menu=gfx_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Debug Panel 🐛", command=self.open_debug_panel)
        tools_menu.add_command(label="Input Config 🎮", command=self.open_input_config)
        tools_menu.add_command(label="Audio Settings 🎧", command=self.open_audio_settings)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About ℹ️", command=self.show_about)
        help_menu.add_command(label="Controls 🎮", command=self.show_controls)
        menubar.add_cascade(label="Help", menu=help_menu)
    
    def setup_main_frame(self):
        """Setup main display area"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for game display
        self.canvas = tk.Canvas(main_frame, bg="black", width=240*2, height=160*2)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Loading label
        self.loading_label = tk.Label(self.canvas, text="Load a ROM to start playing! 🐱🎮", 
                                     font=("Arial", 16), bg="black", fg="white")
        self.loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # FPS display
        self.fps_label = tk.Label(self.canvas, text="FPS: --", font=("Arial", 10), 
                                 bg="black", fg="yellow")
        self.fps_label.place(x=10, y=10)
    
    def setup_side_panel(self):
        """Setup side panel with controls"""
        side_frame = ttk.Frame(self.root)
        side_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Control buttons
        ttk.Button(side_frame, text="Play ⏯️", command=self.toggle_play_pause).pack(fill=tk.X, pady=2)
        ttk.Button(side_frame, text="Reset 🔄", command=self.reset_emu).pack(fill=tk.X, pady=2)
        ttk.Button(side_frame, text="Rewind ⏪", command=lambda: self.emu.rewind(10)).pack(fill=tk.X, pady=2)
        
        # State slots
        ttk.Label(side_frame, text="State Slots:").pack(pady=(10, 2))
        state_frame = ttk.Frame(side_frame)
        state_frame.pack()
        
        for i in range(5):
            btn_frame = ttk.Frame(state_frame)
            btn_frame.pack(pady=1)
            ttk.Button(btn_frame, text=f"Save {i}", width=6,
                      command=lambda s=i: self.emu.save_state(s)).pack(side=tk.LEFT)
            ttk.Button(btn_frame, text=f"Load {i}", width=6,
                      command=lambda s=i: self.emu.load_state(s)).pack(side=tk.LEFT)
        
        # Speed control
        ttk.Label(side_frame, text="Speed:").pack(pady=(10, 2))
        speed_scale = ttk.Scale(side_frame, from_=0.1, to=5.0, variable=self.speed_var,
                               command=lambda v: self.update_speed())
        speed_scale.pack(fill=tk.X)
        
        # Frame skip
        ttk.Label(side_frame, text="Frame Skip:").pack(pady=(10, 2))
        frame_scale = ttk.Scale(side_frame, from_=0, to=9, variable=self.frame_skip_var,
                               command=lambda v: self.update_frame_skip())
        frame_scale.pack(fill=tk.X)
    
    def setup_status_bar(self):
        """Setup status bar at bottom"""
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="Ready~ Load a ROM to start! 🐱")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.rom_label = ttk.Label(status_frame, text="No ROM loaded")
        self.rom_label.pack(side=tk.RIGHT, padx=5)
    
    def setup_key_bindings(self):
        """Setup keyboard bindings"""
        # GBA controls
        key_map = {
            'z': 'A', 'x': 'B', 'Return': 'START', 'Shift_L': 'SELECT',
            'Up': 'UP', 'Down': 'DOWN', 'Left': 'LEFT', 'Right': 'RIGHT',
            'a': 'L', 's': 'R'
        }
        
        for key, button in key_map.items():
            self.root.bind(f"<KeyPress-{key}>", lambda e, k=key: self.key_event(k, True))
            self.root.bind(f"<KeyRelease-{key}>", lambda e, k=key: self.key_event(k, False))
        
        # Control keys
        self.root.bind("<Control-o>", lambda e: self.open_rom())
        self.root.bind("<space>", lambda e: self.toggle_play_pause())
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Function keys for states
        for i in range(5):
            self.root.bind(f"<F{i+1}>", lambda e, s=i: self.emu.save_state(s))
            self.root.bind(f"<Shift-F{i+1}>", lambda e, s=i: self.emu.load_state(s))
    
    def key_event(self, key, pressed):
        """Handle keyboard events"""
        if pressed:
            self.emu.key_down(key)
        else:
            self.emu.key_up(key)
    
    def open_rom(self):
        """Open ROM file dialog"""
        filename = filedialog.askopenfilename(
            title="Select ROM file",
            filetypes=[
                ("GBA ROMs", "*.gba *.agb"),
                ("GB ROMs", "*.gb *.gbc"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.status_label.config(text=f"Loading {os.path.basename(filename)}...")
            self.root.update()
            
            if self.emu.load_rom(filename):
                self.rom_loaded = True
                self.loading_label.destroy()
                self.rom_label.config(text=os.path.basename(filename))
                self.status_label.config(text="ROM loaded! Press Space to start~ 🐱")
                self.emu.running = True
            else:
                messagebox.showerror("Error", "Failed to load ROM!")
                self.status_label.config(text="Failed to load ROM 😿")
    
    def toggle_play_pause(self):
        """Toggle play/pause"""
        if not self.rom_loaded:
            return
        
        self.emu.toggle_pause()
        if self.emu.paused:
            self.status_label.config(text="Paused ⏸️")
        else:
            self.status_label.config(text="Playing ▶️")
    
    def reset_emu(self):
        """Reset emulator"""
        if self.rom_loaded:
            self.emu.cpu.reset()
            self.status_label.config(text="Emulator reset 🔄")
    
    def update_speed(self):
        """Update emulation speed"""
        self.emu.set_speed(self.speed_var.get())
    
    def update_frame_skip(self):
        """Update frame skip setting"""
        self.emu.frame_skip = self.frame_skip_var.get()
    
    def change_filter(self):
        """Change graphics filter"""
        self.emu.filters.current_filter = self.current_filter.get()
    
    def toggle_frameskip(self):
        """Toggle auto frameskip"""
        # Implementation would go here
        pass
    
    def open_cheat_editor(self):
        """Open cheat code editor"""
        editor = tk.Toplevel(self.root)
        editor.title("libmeow0.1 Cheat Editor 🎀")
        editor.geometry("400x300")
        
        # Cheat list
        list_frame = ttk.Frame(editor)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        cheat_list = tk.Listbox(list_frame)
        cheat_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, command=cheat_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        cheat_list.config(yscrollcommand=scrollbar.set)
        
        # Load existing cheats
        for i, cheat in enumerate(self.emu.cheats.active_codes):
            cheat_list.insert(tk.END, 
                            f"{'✓' if cheat['enabled'] else '✗'} {cheat['description']}")
        
        # Control buttons
        btn_frame = ttk.Frame(editor)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Add Cheat ➕", 
                  command=lambda: self.add_cheat_dialog(cheat_list)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Remove Cheat ➖",
                  command=lambda: self.remove_cheat(cheat_list)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Toggle ⚡",
                  command=lambda: self.toggle_cheat(cheat_list)).pack(side=tk.LEFT)
    
    def add_cheat_dialog(self, cheat_list):
        """Dialog to add new cheat"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Cheat Code")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="Cheat Code:").pack(pady=5)
        code_entry = ttk.Entry(dialog, width=30)
        code_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Description:").pack(pady=5)
        desc_entry = ttk.Entry(dialog, width=30)
        desc_entry.pack(pady=5)
        
        def add_cheat():
            code = code_entry.get()
            desc = desc_entry.get()
            if code:
                cheat_id = self.emu.cheats.parse_code(code)
                if cheat_id is not None and desc:
                    self.emu.cheats.active_codes[cheat_id]['description'] = desc
                cheat_list.insert(tk.END, f"✓ {desc or code}")
                dialog.destroy()
        
        ttk.Button(dialog, text="Add", command=add_cheat).pack(pady=10)
    
    def remove_cheat(self, cheat_list):
        """Remove selected cheat"""
        selection = cheat_list.curselection()
        if selection:
            index = selection[0]
            if index < len(self.emu.cheats.active_codes):
                del self.emu.cheats.active_codes[index]
            cheat_list.delete(index)
    
    def toggle_cheat(self, cheat_list):
        """Toggle selected cheat"""
        selection = cheat_list.curselection()
        if selection:
            index = selection[0]
            if index < len(self.emu.cheats.active_codes):
                cheat = self.emu.cheats.active_codes[index]
                cheat['enabled'] = not cheat['enabled']
                
                # Update list display
                text = cheat_list.get(index)
                if cheat['enabled']:
                    new_text = text.replace('✗', '✓')
                else:
                    new_text = text.replace('✓', '✗')
                cheat_list.delete(index)
                cheat_list.insert(index, new_text)
                cheat_list.selection_set(index)
    
    def save_state_dialog(self):
        """Dialog for saving state"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Save State")
        dialog.geometry("200x150")
        
        ttk.Label(dialog, text="Select Slot:").pack(pady=10)
        
        slot_var = tk.IntVar(value=0)
        for i in range(5):
            ttk.Radiobutton(dialog, text=f"Slot {i}", variable=slot_var, value=i).pack()
        
        def save():
            if self.emu.save_state(slot_var.get()):
                messagebox.showinfo("Success", f"State saved to slot {slot_var.get()}!")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to save state!")
        
        ttk.Button(dialog, text="Save", command=save).pack(pady=10)
    
    def load_state_dialog(self):
        """Dialog for loading state"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Load State")
        dialog.geometry("200x150")
        
        ttk.Label(dialog, text="Select Slot:").pack(pady=10)
        
        slot_var = tk.IntVar(value=0)
        for i in range(5):
            ttk.Radiobutton(dialog, text=f"Slot {i}", variable=slot_var, value=i).pack()
        
        def load():
            if self.emu.load_state(slot_var.get()):
                messagebox.showinfo("Success", f"State loaded from slot {slot_var.get()}!")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to load state!")
        
        ttk.Button(dialog, text="Load", command=load).pack(pady=10)
    
    def open_debug_panel(self):
        """Open debug panel"""
        debug = tk.Toplevel(self.root)
        debug.title("libmeow0.1 Debug Panel 🐛")
        debug.geometry("600x400")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(debug)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # CPU tab
        cpu_frame = ttk.Frame(notebook)
        notebook.add(cpu_frame, text="CPU")
        
        # Registers
        reg_frame = ttk.LabelFrame(cpu_frame, text="Registers")
        reg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.register_labels = {}
        for i in range(16):
            row = i // 8
            col = i % 8
            frame = ttk.Frame(reg_frame)
            frame.grid(row=row, column=col, padx=2, pady=2)
            ttk.Label(frame, text=f"R{i}:", width=3).pack(side=tk.LEFT)
            lbl = ttk.Label(frame, text="0x00000000", width=10)
            lbl.pack(side=tk.LEFT)
            self.register_labels[f"R{i}"] = lbl
        
        # PC and CPSR
        info_frame = ttk.Frame(cpu_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="PC:").pack(side=tk.LEFT, padx=5)
        self.pc_label = ttk.Label(info_frame, text="0x00000000")
        self.pc_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(info_frame, text="CPSR:").pack(side=tk.LEFT, padx=5)
        self.cpsr_label = ttk.Label(info_frame, text="0x00000000")
        self.cpsr_label.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        ctrl_frame = ttk.Frame(cpu_frame)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ctrl_frame, text="Step ▶️", 
                  command=self.emu.debugger.cpu_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="Pause ⏸️", 
                  command=self.emu.debugger.pause).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="Resume ▶️", 
                  command=self.emu.debugger.resume).pack(side=tk.LEFT, padx=2)
        
        # Memory tab
        mem_frame = ttk.Frame(notebook)
        notebook.add(mem_frame, text="Memory")
        
        # Memory viewer
        mem_text = scrolledtext.ScrolledText(mem_frame, width=80, height=20)
        mem_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.memory_text = mem_text
        
        # Breakpoints tab
        bp_frame = ttk.Frame(notebook)
        notebook.add(bp_frame, text="Breakpoints")
        
        bp_list = tk.Listbox(bp_frame)
        bp_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add breakpoint controls
        bp_ctrl = ttk.Frame(bp_frame)
        bp_ctrl.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(bp_ctrl, text="Address:").pack(side=tk.LEFT)
        bp_addr = ttk.Entry(bp_ctrl, width=12)
        bp_addr.pack(side=tk.LEFT, padx=5)
        
        def add_bp():
            try:
                addr = int(bp_addr.get(), 16)
                bp_id = self.emu.debugger.add_breakpoint(addr)
                bp_list.insert(tk.END, f"0x{addr:08X} (#{bp_id})")
                bp_addr.delete(0, tk.END)
            except:
                messagebox.showerror("Error", "Invalid address!")
        
        ttk.Button(bp_ctrl, text="Add", command=add_bp).pack(side=tk.LEFT, padx=5)
        
        def del_bp():
            selection = bp_list.curselection()
            if selection:
                # Extract BP ID from text
                text = bp_list.get(selection[0])
                if '#' in text:
                    bp_id = int(text.split('#')[1].strip(')'))
                    self.emu.debugger.remove_breakpoint(bp_id)
                    bp_list.delete(selection[0])
        
        ttk.Button(bp_ctrl, text="Remove", command=del_bp).pack(side=tk.LEFT, padx=5)
    
    def open_input_config(self):
        """Open input configuration dialog"""
        config = tk.Toplevel(self.root)
        config.title("Input Configuration 🎮")
        config.geometry("400x300")
        
        # Create input mapping table
        tree = ttk.Treeview(config, columns=('Key', 'Action'), show='headings')
        tree.heading('Key', text='Key')
        tree.heading('Action', text='Action')
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load current mappings
        for key, action in self.emu.joypad.keyboard_map.items():
            tree.insert('', tk.END, values=(key.upper(), action))
        
        # Control buttons
        btn_frame = ttk.Frame(config)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        def remap():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                key = item['values'][0].lower()
                
                # Wait for new key press
                config.bind('<Key>', lambda e: self.update_key_mapping(e, key, tree, selection[0]))
                tree.item(selection[0], values=(f"Press key...", item['values'][1]))
        
        ttk.Button(btn_frame, text="Remap", command=remap).pack(side=tk.LEFT, padx=5)
        
        def reset_mappings():
            self.emu.joypad.keyboard_map = {
                'z': 'A', 'x': 'B', 'enter': 'START', 'shift': 'SELECT',
                'up': 'UP', 'down': 'DOWN', 'left': 'LEFT', 'right': 'RIGHT',
                'a': 'L', 's': 'R'
            }
            
            # Update tree
            for item in tree.get_children():
                tree.delete(item)
            
            for key, action in self.emu.joypad.keyboard_map.items():
                tree.insert('', tk.END, values=(key.upper(), action))
        
        ttk.Button(btn_frame, text="Reset Defaults", command=reset_mappings).pack(side=tk.LEFT, padx=5)
    
    def update_key_mapping(self, event, old_key, tree, item_id):
        """Update key mapping after remap"""
        new_key = event.keysym.lower()
        
        # Find which action this key was mapped to
        for child in tree.get_children():
            values = tree.item(child)['values']
            if values[0].lower() == old_key:
                action = values[1]
                self.emu.joypad.keyboard_map[new_key] = action
                if old_key in self.emu.joypad.keyboard_map:
                    del self.emu.joypad.keyboard_map[old_key]
                tree.item(item_id, values=(new_key.upper(), action))
                break
        
        # Unbind the temporary handler
        event.widget.master.unbind('<Key>')
    
    def open_audio_settings(self):
        """Open audio settings dialog"""
        audio = tk.Toplevel(self.root)
        audio.title("Audio Settings 🎧")
        audio.geometry("300x200")
        
        # Volume control
        ttk.Label(audio, text="Volume:").pack(pady=(10, 0))
        volume_scale = ttk.Scale(audio, from_=0, to=100, 
                                command=lambda v: self.update_audio_volume(float(v)/100))
        volume_scale.set(self.emu.audio.volume * 100)
        volume_scale.pack(fill=tk.X, padx=20, pady=5)
        
        # Audio filters
        filter_frame = ttk.LabelFrame(audio, text="Audio Filters")
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        lowpass_var = tk.BooleanVar(value=self.emu.audio.audio_filters['lowpass'])
        echo_var = tk.BooleanVar(value=self.emu.audio.audio_filters['echo'])
        
        ttk.Checkbutton(filter_frame, text="Low Pass Filter", 
                       variable=lowpass_var,
                       command=lambda: self.update_audio_filter('lowpass', lowpass_var.get())).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Checkbutton(filter_frame, text="Echo", 
                       variable=echo_var,
                       command=lambda: self.update_audio_filter('echo', echo_var.get())).pack(anchor=tk.W, padx=5, pady=2)
        
        # Mute button
        mute_var = tk.BooleanVar(value=self.emu.audio.muted)
        ttk.Checkbutton(audio, text="Mute", 
                       variable=mute_var,
                       command=lambda: self.toggle_audio_mute(mute_var.get())).pack(pady=10)
    
    def update_audio_volume(self, volume):
        """Update audio volume"""
        self.emu.audio.volume = volume
    
    def update_audio_filter(self, filter_name, enabled):
        """Update audio filter"""
        self.emu.audio.audio_filters[filter_name] = enabled
    
    def toggle_audio_mute(self, muted):
        """Toggle audio mute"""
        self.emu.audio.muted = muted
    
    def show_about(self):
        """Show about dialog"""
        about = tk.Toplevel(self.root)
        about.title("About CatGBAEmuHDRV0")
        about.geometry("400x300")
        
        about_text = """
CatGBAEmuHDRV0 with libmeow0.1 Core
        
A Wholesome Pwny Council Production 🐱🍓💕
        
Features:
• GBA/GB/GBC Emulation
• VBA-M Style Cheat System
• Graphics Filters & Effects
• Save States & Rewind
• Debugging Tools
• Customizable Controls
        
License: Hugware v2.0
Free to use with love and strawberry milk~
        
Made with ❤️ by the Pwny Council
        """
        
        text_widget = tk.Text(about, wrap=tk.WORD, bg=about.cget('bg'), 
                             relief=tk.FLAT, font=("Arial", 10))
        text_widget.insert(1.0, about_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def show_controls(self):
        """Show controls dialog"""
        controls = tk.Toplevel(self.root)
        controls.title("Controls 🎮")
        controls.geometry("300x400")
        
        controls_text = """
Default Controls:
        
Movement:
↑↓←→ - D-Pad
        
Buttons:
Z - A Button
X - B Button
A - L Trigger
S - R Trigger
Enter - START
Shift - SELECT
        
System:
Space - Play/Pause
F1-F5 - Save State (Shift to Load)
Ctrl+O - Open ROM
Esc - Exit
        
Cheats:
Use Cheat Editor in menu
        
Debug:
F12 - Open Debug Panel
        """
        
        text_widget = tk.Text(controls, wrap=tk.WORD, bg=controls.cget('bg'),
                             relief=tk.FLAT, font=("Courier", 10))
        text_widget.insert(1.0, controls_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def update(self):
        """Main update loop"""
        if self.rom_loaded and self.emu.running and not self.emu.paused:
            # Run one frame
            frame_data = self.emu.run_frame()
            
            if frame_data:
                # Update display
                self.update_display(frame_data)
                
                # Update FPS
                fps = self.emu.ppu.get_fps()
                if fps > 0:
                    self.fps_label.config(text=f"FPS: {fps:.1f}")
                
                # Update debug info if panel is open
                self.update_debug_info()
            
            # Update status
            if self.emu.debugger.paused:
                self.status_label.config(text="Debug Paused ⏸️")
        
        # Schedule next update
        self.root.after(self.update_interval, self.update)
    
    def update_display(self, frame_data):
        """Update canvas with frame data"""
        # Convert to PhotoImage (simplified - would need proper conversion)
        # For now, just show a placeholder
        if not hasattr(self, 'display_image'):
            # Create a simple colored rectangle for demonstration
            self.canvas.delete("all")
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width > 1 and height > 1:
                # Draw a simple representation
                scale_x = width / 240
                scale_y = height / 160
                
                # Draw some colored rectangles to simulate game
                colors = ['red', 'green', 'blue', 'yellow', 'purple', 'cyan']
                for i in range(6):
                    x1 = i * 40 * scale_x
                    y1 = 0
                    x2 = (i + 1) * 40 * scale_x
                    y2 = height
                    self.canvas.create_rectangle(x1, y1, x2, y2, 
                                               fill=colors[i], outline='')
        
        # In a real implementation, you would convert frame_data to PhotoImage
        # and display it on the canvas
    
    def update_debug_info(self):
        """Update debug panel information"""
        if hasattr(self, 'pc_label'):
            # Update CPU registers
            cpu_state = self.emu.debugger.get_cpu_state()
            
            if 'pc' in cpu_state:
                self.pc_label.config(text=cpu_state['pc'])
            
            if 'registers' in cpu_state and len(cpu_state['registers']) >= 16:
                for i in range(16):
                    label = self.register_labels.get(f"R{i}")
                    if label and i < len(cpu_state['registers']):
                        label.config(text=cpu_state['registers'][i])
            
            # Update memory viewer occasionally
            if hasattr(self, 'memory_text'):
                current_time = time.time()
                if not hasattr(self, 'last_memory_update') or current_time - self.last_memory_update > 1.0:
                    memory_data = self.emu.debugger.read_memory(0x02000000, 256)
                    hex_dump = self.format_hex_dump(memory_data, 0x02000000)
                    self.memory_text.delete(1.0, tk.END)
                    self.memory_text.insert(1.0, hex_dump)
                    self.last_memory_update = current_time
    
    def format_hex_dump(self, data, base_address):
        """Format memory data as hex dump"""
        result = ""
        bytes_per_line = 16
        
        for i in range(0, len(data), bytes_per_line):
            # Address
            result += f"{base_address + i:08X}: "
            
            # Hex bytes
            hex_bytes = ""
            ascii_bytes = ""
            
            for j in range(bytes_per_line):
                if i + j < len(data):
                    byte = data[i + j]
                    hex_bytes += f"{byte:02X} "
                    
                    # ASCII representation
                    if 32 <= byte <= 126:
                        ascii_bytes += chr(byte)
                    else:
                        ascii_bytes += "."
                else:
                    hex_bytes += "   "
                    ascii_bytes += " "
            
            result += f"{hex_bytes:48} {ascii_bytes}\n"
        
        return result
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

# ======================
# MAIN ENTRY POINT
# ======================

def main():
    """Main function"""
    print("""
    ╔═══════════════════════════════════════════╗
    ║   CatGBAEmuHDRV0 with libmeow0.1 Core     ║
    ║   Wholesome Pwny Council Edition 🐱🍓💕   ║
    ╚═══════════════════════════════════════════╝
    """)
    
    gui = CatEMUGUI()
    gui.run()

if __name__ == "__main__":
    main()
