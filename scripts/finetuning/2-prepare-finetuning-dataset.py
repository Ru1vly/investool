#!/usr/bin/env python3
"""
============================================================================
Phase 3.2: Prepare Fine-Tuning Dataset

Converts exported PostgreSQL data into JSONL format for Gemini fine-tuning.
Includes data cleaning, validation, and quality checks.
============================================================================
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse


def load_raw_data(input_file: str) -> List[Dict[str, Any]]:
    """Load raw JSON data from export."""
    print(f"Loading data from: {input_file}")

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Handle PostgreSQL json_agg output (array or nested array)
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
        data = data[0]

    print(f"✅ Loaded {len(data)} examples")
    return data


def validate_example(example: Dict[str, Any]) -> tuple[bool, str]:
    """Validate a single training example."""

    # Check required fields
    if 'strategy_input' not in example or 'analysis_output' not in example:
        return False, "Missing required fields"

    strategy = example['strategy_input']
    analysis = example['analysis_output']

    # Check for empty content
    if not strategy or not analysis:
        return False, "Empty strategy or analysis"

    # Check minimum length (avoid trivial examples)
    if len(strategy) < 50:
        return False, f"Strategy too short ({len(strategy)} chars)"

    if len(analysis) < 100:
        return False, f"Analysis too short ({len(analysis)} chars)"

    # Check maximum length (Gemini limits)
    if len(strategy) > 30000:
        return False, f"Strategy too long ({len(strategy)} chars)"

    if len(analysis) > 30000:
        return False, f"Analysis too long ({len(analysis)} chars)"

    # Check for potential errors in analysis
    error_indicators = ['error', 'exception', 'failed', 'cannot', 'unable']
    analysis_lower = analysis.lower()
    if any(indicator in analysis_lower for indicator in error_indicators):
        # Only reject if it seems like an error message (not just mentioning errors)
        if analysis_lower.startswith('error') or 'traceback' in analysis_lower:
            return False, "Analysis contains error message"

    return True, "OK"


def convert_to_gemini_format(example: Dict[str, Any]) -> Dict[str, Any]:
    """Convert example to Gemini fine-tuning format."""

    # Gemini fine-tuning format: text_input and output
    return {
        "text_input": example['strategy_input'],
        "output": example['analysis_output']
    }


def clean_and_prepare_dataset(
    raw_data: List[Dict[str, Any]],
    max_examples: int = None
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Clean, validate, and prepare dataset."""

    print("\n" + "="*70)
    print("  Data Cleaning and Validation")
    print("="*70 + "\n")

    valid_examples = []
    invalid_examples = []
    stats = {
        'total': len(raw_data),
        'valid': 0,
        'invalid': 0,
        'invalid_reasons': {}
    }

    for idx, example in enumerate(raw_data):
        is_valid, reason = validate_example(example)

        if is_valid:
            gemini_example = convert_to_gemini_format(example)
            valid_examples.append(gemini_example)
            stats['valid'] += 1
        else:
            invalid_examples.append({
                'example_id': example.get('id', idx),
                'reason': reason
            })
            stats['invalid'] += 1
            stats['invalid_reasons'][reason] = stats['invalid_reasons'].get(reason, 0) + 1

    # Limit to max_examples if specified
    if max_examples and len(valid_examples) > max_examples:
        print(f"⚠️  Limiting to {max_examples} examples (from {len(valid_examples)})")
        valid_examples = valid_examples[:max_examples]
        stats['limited_to'] = max_examples

    return valid_examples, stats


def save_jsonl(data: List[Dict[str, Any]], output_file: str):
    """Save data in JSONL format (one JSON object per line)."""

    with open(output_file, 'w') as f:
        for example in data:
            f.write(json.dumps(example) + '\n')

    print(f"✅ Saved {len(data)} examples to: {output_file}")


def print_statistics(stats: Dict[str, Any], valid_examples: List[Dict[str, Any]]):
    """Print dataset statistics."""

    print("\n" + "="*70)
    print("  Dataset Statistics")
    print("="*70 + "\n")

    print(f"Total examples processed: {stats['total']}")
    print(f"Valid examples: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
    print(f"Invalid examples: {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")

    if stats['invalid'] > 0:
        print("\nInvalid example reasons:")
        for reason, count in stats['invalid_reasons'].items():
            print(f"  • {reason}: {count}")

    if valid_examples:
        # Calculate length statistics
        input_lengths = [len(ex['text_input']) for ex in valid_examples]
        output_lengths = [len(ex['output']) for ex in valid_examples]

        print(f"\nInput (strategy) length statistics:")
        print(f"  • Min: {min(input_lengths)} chars")
        print(f"  • Max: {max(input_lengths)} chars")
        print(f"  • Average: {sum(input_lengths)/len(input_lengths):.0f} chars")

        print(f"\nOutput (analysis) length statistics:")
        print(f"  • Min: {min(output_lengths)} chars")
        print(f"  • Max: {max(output_lengths)} chars")
        print(f"  • Average: {sum(output_lengths)/len(output_lengths):.0f} chars")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare fine-tuning dataset for Gemini"
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input JSON file from export'
    )
    parser.add_argument(
        '--output-dir',
        default='./training_data',
        help='Output directory for JSONL files'
    )
    parser.add_argument(
        '--max-examples',
        type=int,
        help='Maximum number of examples to include'
    )
    parser.add_argument(
        '--train-split',
        type=float,
        default=0.9,
        help='Train/validation split ratio (default: 0.9)'
    )

    args = parser.parse_args()

    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  Phase 3.2: Prepare Fine-Tuning Dataset".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝\n")

    # Load raw data
    raw_data = load_raw_data(args.input)

    # Clean and prepare
    valid_examples, stats = clean_and_prepare_dataset(
        raw_data,
        max_examples=args.max_examples
    )

    if not valid_examples:
        print("\n❌ No valid examples found!")
        sys.exit(1)

    # Print statistics
    print_statistics(stats, valid_examples)

    # Split into train/validation
    split_idx = int(len(valid_examples) * args.train_split)
    train_examples = valid_examples[:split_idx]
    val_examples = valid_examples[split_idx:]

    print(f"\nDataset split:")
    print(f"  • Training: {len(train_examples)} examples ({len(train_examples)/len(valid_examples)*100:.1f}%)")
    print(f"  • Validation: {len(val_examples)} examples ({len(val_examples)/len(valid_examples)*100:.1f}%)")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save training set
    train_file = output_dir / f"training_set_{timestamp}.jsonl"
    save_jsonl(train_examples, str(train_file))

    # Save validation set
    val_file = output_dir / f"validation_set_{timestamp}.jsonl"
    save_jsonl(val_examples, str(val_file))

    # Save metadata
    metadata = {
        'created_at': datetime.now().isoformat(),
        'input_file': args.input,
        'total_examples': len(valid_examples),
        'train_examples': len(train_examples),
        'validation_examples': len(val_examples),
        'train_split': args.train_split,
        'statistics': stats,
        'train_file': str(train_file.name),
        'validation_file': str(val_file.name)
    }

    metadata_file = output_dir / f"dataset_metadata_{timestamp}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Metadata saved: {metadata_file}")

    # Print summary
    print("\n" + "="*70)
    print("  ✅ Dataset Preparation Complete!")
    print("="*70 + "\n")

    print("Output files:")
    print(f"  • Training: {train_file}")
    print(f"  • Validation: {val_file}")
    print(f"  • Metadata: {metadata_file}")

    print("\nNext steps:")
    print("  1. Review sample examples in the JSONL files")
    print("  2. Upload training_set.jsonl to Google AI Studio")
    print("  3. Create fine-tuning job")
    print("  4. Run: ./scripts/finetuning/3-create-finetuning-job.sh")
    print("")


if __name__ == '__main__':
    main()
