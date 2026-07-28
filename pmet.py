#!/usr/bin/env python3

"""
pmet.py

Comand-line interface for the PMET program.

This module parses command-line arguments, preforms basic input
validation, and delegates the actual processing work to
:func:'src.main.run'.

:Usage:

.. code-block:: console

    $ python pmet.py -i /path/to/input -o /path/to/output -w 4

"""

import os
import argparse
from typing import Any

import src.main as main

TITLE: str = r"""
  ____  __  __   _____ _____
 |  _ \|  \/  | | ____|_   _|
 | |_) | |\/| | |  _|   | |
 |  __/| |  | |_| |___ _| |
 |_| (_)_|  |_(_)_____(_)_|
Point-based Model Evaluation Tool

Please put on your 3d glasses now.
"""


def pmet() -> None:
    """
    Run the command-line interface for the PMET program.

    Parses command-line arguments, validates the provided input
    directory exists, builds the argument dictionary, and invokes
    :func:'src.main.run'.

    :param -i, --input: Path to the input directory containing
        the data/models to evaluate. **Required.**
    :type -i, --input: str

    :param -o, --output: Path to the output directory where results
        will be written. Optional; if not specified the default behavior
        of :func:'src.main.run' is used.
    :type -o, --output: str

    :param -w, --workers: Maximum number of parallel processes to use.
        Optional; if not specified the default behavior of :func:'src.main.run'
        is used.
    :type -w, --workers: int

    :param -p, --border-padding: Number of pixels to shrink the sample border by.
    :type -p, --border-padding: int

    :param -b, --bar: Enable or disable the status bar.
    :type -b, --bar: bool

    :raises SystemExit: If no input directory is provided, or if the provided directory
        does not exist on disk. In both cases the program will exit.
    """
    parser = argparse.ArgumentParser(description="Point-based Model Evaluation Tool")

    _ = parser.add_argument("-i", "--input", type=str, help="input directory")
    _ = parser.add_argument("-o", "--output", type=str, help="output directory")
    _ = parser.add_argument(
        "-w", "--workers", type=int, help="maximum number of parallel processes"
    )
    _ = parser.add_argument(
        "-p",
        "--border-padding",
        type=int,
        help="Number of pixels to shrink the sample border by",
    )
    _ = parser.add_argument(
        "-n", "--no-progress", action="store_true", help="Disable the progress bar"
    )

    # Hidden cheat code argument
    _ = parser.add_argument("cheatcode", nargs="?", help=argparse.SUPPRESS)

    args = parser.parse_args()

    # Small easter egg
    if args.cheatcode == "uuddlrlrba":
        # Super mode activated!
        print(
            "[31mS[0m[33mU[0m[32mP[0m[36mE[0m[34mR[0m [35mM[0m[31mO[0m[33mD[0m[32mE[0m [36mA[0m[34mC[0m[35mT[0m[31mI[0m[33mV[0m[32mA[0m[36mT[0m[34mE[0m[35mD[0m[31m![0m"
        )
        print(TITLE[::-1])
    else:
        print(TITLE)

    kwargs: dict[str, Any] = {
        "root_dir": args.input,
    }

    if args.output:
        kwargs["output_dir"] = args.output
    if args.workers:
        kwargs["max_workers"] = args.workers
    if args.border_padding:
        kwargs["sample_area_padding"] = args.border_padding
    if args.no_progress:
        kwargs["no_progress"] = args.no_progress

    # Input validation
    if not args.input:
        print("No input directory specified!")
        print("Try '-h' or '--help' for more information.")
        exit()

    if not os.path.isdir(kwargs["root_dir"]):
        print(f"Invalid directory {kwargs['root_dir']} entered!")
        print("Please check your parameters and try again.")
        exit()

    main.run(**kwargs)

    print("Processing complete!")
    print("Thank you for using PMET, You can now take off your 3d glasses.")


if __name__ == "__main__":
    pmet()
