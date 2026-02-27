"""Whiteprint CLI - Generate UML diagrams from source code."""

import sys
from pathlib import Path

import click

from whiteprint.exporters.drawio import export_uml
from whiteprint.model import RelationshipDetector
from whiteprint.parsers import (
    detect_language_from_extension,
    get_parser_for_language,
)


@click.command()
@click.argument("source_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path (default: same as source with .drawio extension)",
)
@click.option(
    "--include-tests",
    is_flag=True,
    default=False,
    help="Include test files in analysis",
)
@click.option(
    "--language",
    "-l",
    type=click.Choice(["python", "rust", "auto"]),
    default="auto",
    help="Source code language (default: auto-detect)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output",
)
def main(
    source_path: str, output: str | None, include_tests: bool, language: str, verbose: bool
) -> None:
    """Generate UML class diagrams from source code.

    SOURCE_PATH: Path to a source file or directory containing source files.
    """
    source = Path(source_path)

    if language == "auto":
        if source.is_file():
            detected = detect_language_from_extension(source)
            if detected:
                language = detected
            else:
                click.echo(
                    "Error: Could not auto-detect language. Please specify with --language.",
                    err=True,
                )
                sys.exit(1)
        else:
            ext_to_lang = {".py": "python", ".rs": "rust"}
            for ext, lang in ext_to_lang.items():
                files = list(source.rglob(f"*{ext}"))
                if files:
                    language = lang
                    break
            else:
                click.echo(
                    "Error: Could not auto-detect language. Please specify with --language.",
                    err=True,
                )
                sys.exit(1)

    if verbose:
        click.echo(f"Using language: {language}")

    parser_class = get_parser_for_language(language)
    parser = parser_class()

    if source.is_file():
        classes = parser.parse(source)
    else:
        classes = parser.parse_directory(source, include_tests=include_tests)

    if not classes:
        click.echo("Warning: No classes found in source.", err=True)
        sys.exit(0)

    if verbose:
        click.echo(f"Found {len(classes)} classes")

    detector = RelationshipDetector(language=language)
    relationships = detector.detect(classes)

    if verbose:
        click.echo(f"Found {len(relationships)} relationships")
        for rel in relationships:
            click.echo(f"  {rel}")

    if output is None:
        if source.is_file():
            output_path = source.with_suffix(".drawio")
        else:
            output_path = source / "uml.drawio"
    else:
        output_path = Path(output).absolute()

    export_uml(classes, relationships, output_path)
    click.echo(f"UML diagram exported to: {output_path}")


if __name__ == "__main__":
    main()
