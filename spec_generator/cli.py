"""
Command-line interface for the specification generator.
"""
import os
import argparse
from typing import Optional
from pathlib import Path

from spec_generator.output import generate_spec_files, generate_common_props_spec

def main(args: Optional[argparse.Namespace] = None) -> None:
    """Main entry point for the specification generator.
    
    Args:
        args: Command-line arguments
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Generate component specifications")
        parser.add_argument(
            "--base-dir", 
            type=str, 
            default=os.getcwd(),
            help="Base directory of the Reflex codebase"
        )
        parser.add_argument(
            "--specs-dir", 
            type=str, 
            default="specs",
            help="Directory to save spec files to"
        )
        parser.add_argument(
            "--clean", 
            action="store_true",
            help="Clean the specs directory before generating new specs"
        )
        parser.add_argument(
            "--only-common-props", 
            action="store_true",
            help="Only generate the common props specification"
        )
        args = parser.parse_args()
    
    base_dir = args.base_dir
    specs_dir = args.specs_dir
    
    # Create the specs directory if it doesn't exist
    os.makedirs(specs_dir, exist_ok=True)
    
    # Clean the specs directory if requested
    if args.clean:
        print(f"Cleaning specs directory: {specs_dir}")
        for file in Path(specs_dir).glob("*.json"):
            file.unlink()
    
    # Generate specs
    if args.only_common_props:
        print("Generating only common props specification...")
        generate_common_props_spec(specs_dir)
    else:
        print(f"Generating component specifications...")
        print(f"Base directory: {base_dir}")
        print(f"Specs directory: {specs_dir}")
        generate_spec_files(base_dir, specs_dir)

if __name__ == "__main__":
    main() 