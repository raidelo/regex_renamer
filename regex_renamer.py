import argparse
import os
import re

EXTENSION_PATTERN = r"\.\w*$"
COLOR_OF_MATCHES = "\033[41m"
COLOR_OF_SUBSTITUTIONS = "\033[42m"
RESET_COLOR = "\033[49m"


def compare_paths(p1: str, p2: str) -> bool:
    """
    Checks if 2 paths are the same, returns `True` or `Flase`.
    It considers '/' and '\\' as the same.
    
    :p1: path 1
    :p2: path 2
    """
    psep = ["\\", "/"]
    if len(p1) != len(p2):
        return False
    for x, y in zip(p1, p2):
        if x in psep and y in psep:
            continue
        elif x == y:
            continue
        else:
            return False
    return True


def format_match(
    pattern: str,
    string: str,
    color: str = COLOR_OF_MATCHES,
    reset_color: str = RESET_COLOR,
) -> str:
    """
    Searches for a `pattern` in a `string` and formats what is found with a given color.
    
    :pattern:    pattern to search for (regular expressions are allowed)
    :string:    the string where the pattern will be attempted to be found
    :color:    the color to format the pattern found with
    :reset_color:    the color to reset the rest of the string that does'nt match with the pattern
    """
    to_return = ""
    prev_end = 0
    matches = tuple(re.finditer(pattern, string))
    if matches:
        for match in matches:
            to_return += (
                string[prev_end : match.start()]
                + color
                + string[match.start() : match.end()]
                + reset_color
            )
            prev_end = match.end()
        to_return += string[prev_end:]
    else:
        to_return += string
    return to_return


def format_substitution(
    pattern: str,
    subs: str,
    string: str,
    color: str = COLOR_OF_SUBSTITUTIONS,
    reset_color: str = RESET_COLOR,
) -> str:
    """
    Searches for a `pattern` in a `string`, makes a substitution with the value of the argument `subs`, formats what is substituted with a given color and returns the resulting string.
    
    :pattern:    pattern to search for (regular expressions are allowed)
    :subs:    substitution string
    :string:    the string where the pattern will be attempted to be found
    :color:    the color to format the pattern found with
    :reset_color:    the color to reset the rest of the string that does'nt match with the pattern
    """
    return re.sub(pattern, color + subs + reset_color, string)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("pattern", metavar="<pattern>")

    parser.add_argument("replacement", metavar="<replacement>", nargs="?")

    parser.add_argument(
        "-p",
        metavar="<path>",
        dest="path",
        default=os.getcwd() + "/",
        help="custom folder path (default: <current working directory>)",
    )

    parser.add_argument(
        "-x",
        "--ignore-ext",
        dest="ignore_extension",
        action="store_true",
        help="to ignore the extension of a file in the replacement (default: False)",
    )

    parser.add_argument(
        "-d",
        "--delete",
        dest="delete",
        action="store_true",
        help="to delete all matches with the pattern (default: False)",
    )

    parser.add_argument(
        "-t",
        "--test",
        dest="test",
        action="store_true",
        help="do not rename files or folders, instead only show what the program would do (default: False)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="count",
        default=0,
        help="do not print the result of the substitutions, if any (default: False)",
    )

    p_grp1 = parser.add_mutually_exclusive_group()

    p_grp1.add_argument(
        "--files",
        "--only-files",
        dest="only_files",
        action="store_true",
        help="to rename files only (default: False)",
    )

    p_grp1.add_argument(
        "--folders",
        "--only-folders",
        dest="only_folders",
        action="store_true",
        help="to rename folders only (default: False)",
    )

    args = parser.parse_args()

    listdir = os.listdir(args.path)

    data = {
        "files": [],
        "folders": [],
        "files_matching": 0,
        "folders_matching": 0,
    }

    # Doing pre-discovering.
    for whatever in listdir:
        if os.path.isdir(whatever):
            data["folders"].append(whatever)
            if re.search(args.pattern, whatever):
                data["folders_matching"] += 1
        else:
            data["files"].append(whatever)
            if re.search(args.pattern, whatever):
                data["files_matching"] += 1

    folders_available = args.only_folders or not args.only_files
    files_available = args.only_files or not args.only_folders

    current = 1
    total_matching = (data["files_matching"] if files_available else 0) + (
        data["folders_matching"] if folders_available else 0
    )

    for name in listdir:
        old_name, new_name, ext = name, name, ""

        # If the `only-files` flag is present, check if `name` is a file, or, if the `only-folder` flag is present, check if `name` is a folder.
        if (args.only_files and not os.path.isfile(name)) or (
            args.only_folders and not os.path.isdir(name)
        ):
            continue
        # If the current directory is the same of the program itself, make sure that this program is not considered.
        if compare_paths(
            os.path.dirname(__file__), os.path.dirname(args.path)
        ) and __file__.endswith(name):
            continue

        # If the `ignore-extension` flag is present and the current `name` is not a folder, extract the extension of the file and remove it from it's name.
        if args.ignore_extension and not os.path.isdir(name):
            pos = re.search(EXTENSION_PATTERN, name)
            if pos:
                name, ext = name[: pos.start()], name[pos.start() :]

        # If neither the `replacement` argument nor the `delete` flag are present, then print the files that match with the `pattern`.
        if not args.replacement and not args.delete:
            print(format_match(args.pattern, name))
            continue
        # If the `delete` flag is present, change the value of the `replacement` argument to a empty string.
        elif args.delete:
            args.replacement = ""

        # Try to replace the `pattern` with the `replacement` string.
        new_name = re.sub(args.pattern, args.replacement, name) + (
            ext if not os.path.isdir(name) else ""
        )

        # If there is a change between the old name of the file/folder and the new name of it, then ...
        if old_name != new_name:

            # Rename the file/folder if the `test` flag is not present.
            if not args.test:
                os.rename(old_name, new_name)

            # Print the result of the renaming.
            if not args.quiet:
                print(
                    "{}: {}/{}".format(
                        "Substitution" if args.test else "Done substitution",
                        current,
                        total_matching,
                    )
                )
                print("Old: {}".format(format_match(args.pattern, name) + ext))
                print(
                    "New: {}\n".format(
                        format_substitution(args.pattern, args.replacement, name) + ext
                    )
                )

                current += 1

    print()
    
    if folders_available and args.quiet < 2:
        print("Total folders: {}".format(len(data["folders"])))
        print("Total folders matching pattern: {}".format(data["folders_matching"]))
    if files_available and args.quiet < 2:
        print("Total files: {}".format(len(data["files"])))
        print("Total files matching pattern: {}".format(data["files_matching"]))
