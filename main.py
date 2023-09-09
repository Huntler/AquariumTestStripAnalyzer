import argparse, os
from reference_table import ReferenceTable
from test_strip import TestStrip


data_folder = "data/"
reference_folder = "reference/"
debugging_folder = "debugging/"


parser = argparse.ArgumentParser(
    prog="Aquarium Test-Strip Analyzer (ATSA)",
    description="The program extracts a water quality test strip of an image, performs white balancing, and compares the color values to a reference table.",
)

parser.add_argument(
    "-i", "--input", help="The path to the input-image of a test strip."
)
parser.add_argument(
    "-r",
    "--reference-table",
    default=f"{data_folder}{reference_folder}default.json",
    help="Overwrites the default reference table.",
)
parser.add_argument(
    "-s",
    "--store-pipeline",
    action="store_true",
    default=False,
    help="Stores the image of each processing step to a subfolder. Useful for debugging.",
)

args = parser.parse_args()

# check if path exists and directs to a valid file
allowed_file_types = ["jpg", "png"]
if (
    not os.path.exists(args.input)
    or not os.path.isfile(args.input)
    or str.split(args.input, ".")[-1].lower() not in allowed_file_types
):
    print("Given input path is wrong. Expecting an image (jpg, png).")
    exit(1)

# check if reference data base exists
allowed_file_types = ["json"]
if (
    not os.path.exists(args.reference_table)
    or not os.path.isfile(args.reference_table)
    or str.split(args.reference_table, ".")[-1].lower() not in allowed_file_types
):
    print("Given input path is wrong. Expecting the reference table (json).")
    exit(1)

# check if debugging folder structure exists
store_pipeline = None
if args.store_pipeline:
    if not os.path.exists(f"{data_folder}{debugging_folder}"):
        os.mkdir(f"{data_folder}{debugging_folder}")

    input_file_name = os.path.splitext(os.path.basename(args.input))[0]
    store_pipeline = f"{data_folder}{debugging_folder}{input_file_name}/"

    if os.path.exists(store_pipeline):
        content = os.listdir(store_pipeline)
        if len(content) > 0:
            [os.remove(f"{store_pipeline}{file}") for file in content]
        os.rmdir(store_pipeline)
    os.mkdir(store_pipeline)

# read the test strip
strip = TestStrip(args.input, debugging_path=store_pipeline)

# read the reference table
table = ReferenceTable(path=args.reference_table)
water_quality = table.analyze_strip(strip)

print(water_quality)
