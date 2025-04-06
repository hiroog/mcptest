#!/usr/bin/env python
import argparse
import asyncio
import datetime
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, BinaryIO

class MCPCommandCapture:
    def __init__(self, command: str, args: List[str], log_dir: str):
        self.command = command
        self.args = args
        self.log_dir = Path(log_dir)
        self.process: Optional[asyncio.subprocess.Process] = None
        self.log_file: Optional[BinaryIO] = None
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_path = self.log_dir / f"mcp-capture-{self.timestamp}.log"
        self.script_log_path = self.log_dir / f"command-capture-{self.timestamp}.log"
        
        # Set up logger for the script itself
        self.setup_logger()

    def setup_logger(self):
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger("command-capture")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(self.script_log_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
    
    async def start(self):
        # Open IO log file
        self.log_file = open(self.log_path, "wb")
        
        # Start the process
        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.logger.info(f"Started process {self.command} with PID {self.process.pid}")
        self.logger.info(f"IO logging to {self.log_path}")
        self.logger.info(f"Script logging to {self.script_log_path}")
        
        # Create tasks for handling stdin, stdout, and stderr
        stdin_task = asyncio.create_task(self.handle_stdin())
        stdout_task = asyncio.create_task(self.handle_stdout())
        stderr_task = asyncio.create_task(self.handle_stderr())
        
        # Wait for process to complete
        await self.process.wait()
        
        # Cancel tasks
        stdin_task.cancel()
        stdout_task.cancel()
        stderr_task.cancel()
        
        # Close log file
        if self.log_file:
            self.log_file.close()
        
        return self.process.returncode

    async def handle_stdin(self):
        assert self.process and self.process.stdin
        assert self.log_file
        
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.buffer.readline
                )
                if not line:
                    break
                
                # Log input with timestamp
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_entry = f"[{timestamp}] IN: {line.decode('utf-8', errors='replace').rstrip()}\n".encode('utf-8')
                self.log_file.write(log_entry)
                self.log_file.flush()
                
                # Forward to process
                self.process.stdin.write(line)
                await self.process.stdin.drain()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error handling stdin: {e}")
                break
        
        # Close stdin if loop breaks
        if not self.process.stdin.is_closing():
            self.process.stdin.close()

    async def handle_stdout(self):
        assert self.process and self.process.stdout
        assert self.log_file
        
        while True:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                # Log output with timestamp
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_entry = f"[{timestamp}] OUT: {line.decode('utf-8', errors='replace').rstrip()}\n".encode('utf-8')
                self.log_file.write(log_entry)
                self.log_file.flush()
                
                # Forward to stdout
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error handling stdout: {e}")
                break

    async def handle_stderr(self):
        assert self.process and self.process.stderr
        assert self.log_file
        
        while True:
            try:
                line = await self.process.stderr.readline()
                if not line:
                    break
                
                # Log error with timestamp
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_entry = f"[{timestamp}] ERR: {line.decode('utf-8', errors='replace').rstrip()}\n".encode('utf-8')
                self.log_file.write(log_entry)
                self.log_file.flush()
                
                # Forward to stderr
                sys.stderr.buffer.write(line)
                sys.stderr.buffer.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error handling stderr: {e}")
                break

def signal_handler(sig, frame):
    logger = logging.getLogger("command-capture")
    logger.info(f"Received signal {sig}, exiting...")
    sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(description="Capture MCP server I/O to log file")
    parser.add_argument("--log-dir", default="./logs", help="Directory to store log files")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output from this script")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the command")
    
    args = parser.parse_args()
    
    # Set up basic console logger if not quiet
    if not args.quiet:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger("command-capture").addHandler(console_handler)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the command capture
    capture = MCPCommandCapture(args.command, args.args, args.log_dir)
    return await capture.start()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
