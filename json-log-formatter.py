import re
import json
import argparse
from pathlib import Path


def format_json_logs(input_file, output_file=None):
    """
    Read a log file with JSON content and reformat it with proper indentation.
    
    Args:
        input_file (str): Path to the input log file
        output_file (str, optional): Path to the output file. If None, print to console.
    """
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    formatted_lines = []
    
    # Regular expression to match timestamp and JSON content
    # Pattern: [YYYY-MM-DD HH:MM:SS.mmm] IN/OUT: {json}
    pattern = r'(\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\] (?:IN|OUT): )(.+)'
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            prefix = match.group(1)
            json_part = match.group(2)
            
            try:
                # Parse the JSON part
                json_obj = json.loads(json_part)
                # Format with indentation
                formatted_json = json.dumps(json_obj, indent=2, ensure_ascii=False)
                # Indent each line of the formatted JSON except the first line
                indented_json = formatted_json.replace('\n', '\n  ')
                # Combine prefix and formatted JSON
                formatted_line = f"{prefix}{indented_json}\n"
            except json.JSONDecodeError:
                # If not valid JSON, keep the original line
                formatted_line = line
        else:
            # If line doesn't match the pattern, keep as is
            formatted_line = line
        
        formatted_lines.append(formatted_line)
    
    # Write to output file or print to console
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(formatted_lines)
        print(f"Formatted log saved to {output_file}")
    else:
        for line in formatted_lines:
            print(line, end='')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format JSON in log files with proper indentation")
    parser.add_argument("input_file", help="Path to the input log file")
    parser.add_argument("-o", "--output", help="Path to the output file (optional)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' does not exist")
        exit(1)
    
    output_path = args.output
    if not output_path and input_path.suffix:
        # Create default output filename by adding '_formatted' before the extension
        stem = input_path.stem
        output_path = str(input_path.with_name(f"{stem}_formatted{input_path.suffix}"))
    
    format_json_logs(args.input_file, output_path)
