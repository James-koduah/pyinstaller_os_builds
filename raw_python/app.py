import re
import sys
import piexif
from PIL import Image
import os
from datetime import datetime
import time
from dotenv import load_dotenv
load_dotenv()


IMAGES_FOLDER = os.getenv("IMAGES_FOLDER", '/')
OUTPUT_LOG_FILE = os.getenv("OUTPUT_LOG_FILE")
SUPRESS_ERRORS = os.getenv("SUPRESS_ERRORS", 'False').lower() in ("true", "1", "yes")
CAMERA_MAKE = os.getenv("CAMERA_MAKE", "Unknown Camera Make")
CAMERA_MODEL = os.getenv("CAMERA_MODEL", "Unknown Camera Model")
WHITEBALANCE = os.getenv("WHITEBALANCE", 0)
FOCAL_LENGTH = os.getenv("FOCAL_LENGTH", 50)
ISO_SPEED = os.getenv("ISO_SPEED", 100)
APERTURE = os.getenv("APERTURE", 28)

FRAME_NUMBER = int(os.getenv('FRAME_NUMBER', 3))
if FRAME_NUMBER == 3:
    FRAME_ORDER = os.getenv("3FRAME_ORDER", "under,over,normal")
else:
    FRAME_ORDER = os.getenv("5FRAME_ORDER", "under,mild_under,normal,mild_over,over")
FRAME_ORDER = FRAME_ORDER.split(',')
VALID_EXTENSIONS = os.getenv("VALID_EXTENSIONS", ".jpg,.tif,.tiff,.png,.jpeg,.dng,.cr2,.nef,.arw")
VALID_EXTENSIONS = VALID_EXTENSIONS.split(',')

UNDER_EXPOSURE_TIME = os.getenv("UNDER_EXPOSURE_TIME", 500)
UNDER_EXPOSURE_BIAS = os.getenv("UNDER_EXPOSURE_BIAS", -2)

MILD_UNDER_EXPOSURE_TIME = os.getenv('MILD_UNDER_EXPOSURE_TIME', 250)
MILD_UNDER_EXPOSURE_BIAS = os.getenv("MILD_UNDER_EXPOSURE_BIAS", -1)

NORMAL_EXPOSURE_TIME = os.getenv("NORMAL_EXPOSURE_TIME", 125)
NORMAL_EXPOSURE_BIAS = os.getenv("NORMAL_EXPOSURE_BIAS", 0)

MILD_OVER_EXPOSURE_TIME= os.getenv("MILD_OVER_EXPOSURE_TIME", 60)
MILD_OVER_EXPOSURE_BIAS=os.getenv("MILD_OVER_EXPOSURE_BIAS", -1)

OVER_EXPOSURE_TIME = os.getenv("OVER_EXPOSURE_TIME", 30)
OVER_EXPOSURE_BIAS = os.getenv("OVER_EXPOSURE_BIAS", 2)



def convert_to_float(name, value):
    try:
        v = float(value)
        return v
    except Exception:
        print(f'Error. {name} must be a number. {value} is not a correct value')

def convert_to_int(name, value):
    try:
        v = int(value)
        return v
    except Exception:
        print(f'Error. {name} must be a number. {value} is not a correct value')



UNDER_EXPOSURE_TIME = convert_to_int("UNDER_EXPOSURE_TIME", UNDER_EXPOSURE_TIME)
UNDER_EXPOSURE_BIAS = convert_to_int("UNDER_EXPOSURE_BIAS", UNDER_EXPOSURE_BIAS)
MILD_UNDER_EXPOSURE_TIME = convert_to_int("MILD_UNDER_EXPOSURE_TIME", MILD_UNDER_EXPOSURE_TIME)
MILD_UNDER_EXPOSURE_BIAS = convert_to_int("MILD_UNDER_EXPOSURE_BIAS", MILD_UNDER_EXPOSURE_BIAS)
NORMAL_EXPOSURE_TIME = convert_to_int("NORMAL_EXPOSURE_TIME", NORMAL_EXPOSURE_TIME)
NORMAL_EXPOSURE_BIAS = convert_to_int("NORMAL_EXPOSURE_BIAS", NORMAL_EXPOSURE_BIAS)
MILD_OVER_EXPOSURE_TIME = convert_to_int("MILD_OVER_EXPOSURE_TIME", MILD_OVER_EXPOSURE_TIME)
MILD_OVER_EXPOSURE_BIAS = convert_to_int("MILD_OVER_EXPOSURE_BIAS", MILD_OVER_EXPOSURE_BIAS)
OVER_EXPOSURE_TIME = convert_to_int("OVER_EXPOSURE_TIME", OVER_EXPOSURE_TIME)
OVER_EXPOSURE_BIAS = convert_to_int("OVER_EXPOSURE_BIAS", OVER_EXPOSURE_BIAS)
WHITEBALANCE = convert_to_int("WHITEBALANCE", WHITEBALANCE)
FOCAL_LENGTH = convert_to_int("FOCAL_LENGTH", FOCAL_LENGTH)
ISO_SPEED = convert_to_int("ISO_SPEED", ISO_SPEED)
APERTURE = convert_to_int("APERTURE", APERTURE)


def preview_mode():
    print('\nHere are the metadata changes to be added to the images:')
    print(f'Camera Make: {CAMERA_MAKE}\nCamera Model: {CAMERA_MODEL}')
    print(f"White Balance: {WHITEBALANCE}\nFocal Length: {FOCAL_LENGTH}mm")
    print(f"ISO Speed Ratings: {ISO_SPEED}\nAperture/FNumber: {APERTURE}/10")

    print('--------- UNDER FRAME ----------')
    print(f'Exposure Time: 1/{UNDER_EXPOSURE_TIME}\nExposure Bias: {UNDER_EXPOSURE_BIAS} EV')

    if FRAME_NUMBER != 3:
        print('--------- MILD UNDER FRAME ----------')
        print(f'Exposure Time: 1/{MILD_UNDER_EXPOSURE_TIME}\nExposure Bias: {MILD_UNDER_EXPOSURE_BIAS} EV')

    print('--------- NORMAL FRAME ----------')
    print(f'Exposure Time: 1/{NORMAL_EXPOSURE_TIME}\nExposure Bias: {NORMAL_EXPOSURE_BIAS} EV')

    if FRAME_NUMBER != 3:
        print('--------- MILD OVER FRAME ----------')
        print(f'Exposure Time: 1/{MILD_OVER_EXPOSURE_TIME}\nExposure Bias: {MILD_OVER_EXPOSURE_BIAS} EV')
    
    print('--------- OVER FRAME ----------')
    print(f'Exposure Time: 1/{OVER_EXPOSURE_TIME}\nExposure Bias: {OVER_EXPOSURE_BIAS} EV')
    
    print("Are you okay with these changes?")
    answer = input("Continue processing? (y/n): ")
    if answer.lower() != 'yes' and answer.lower() != 'y':
        print('Aborting...')
        return False
    return True
    

def validate_config_values():
    # Validate Config Values
    if not IMAGES_FOLDER:
        print("Error. Missing Config Value: IMAGES_FOLDER")
        print("Please Specify the folder containing the images Images in the .env config file")
        return False
    return True


hdr_metadata = {
    "under": {
        "ExposureTime": (1, UNDER_EXPOSURE_TIME),       # Exposure time: 1/200s
        "ExposureBiasValue": (UNDER_EXPOSURE_BIAS, 1),  # Exposure bias: -2 EV
    },
    "mild_under": {
        "ExposureTime": (1, MILD_UNDER_EXPOSURE_TIME),       # Exposure time: 1/200s
        "ExposureBiasValue": (MILD_UNDER_EXPOSURE_BIAS, 1),  # Exposure bias: -2 EV
    },
    "normal": {
        "ExposureTime": (1, NORMAL_EXPOSURE_TIME),      # Exposure time: 1/100s
        "ExposureBiasValue": (NORMAL_EXPOSURE_BIAS, 1),   # Exposure bias: 0 EV
    },
    "mild_over": {
        "ExposureTime": (1, MILD_OVER_EXPOSURE_TIME),       # Exposure time: 1/50s
        "ExposureBiasValue": (MILD_OVER_EXPOSURE_BIAS, 1),   # Exposure bias: +2 EV
    },
    "over": {
        "ExposureTime": (1, OVER_EXPOSURE_TIME),       # Exposure time: 1/50s
        "ExposureBiasValue": (OVER_EXPOSURE_BIAS, 1),   # Exposure bias: +2 EV
    },
}

# "FNumber": (APERTURE, 10),           # Aperture: f/2.8
# "ISOSpeedRatings": ISO_SPEED,        # ISO 100

def add_exif(image_path, type, date):
    metadata = hdr_metadata.get(type)
    if not metadata:
        return
    
    # Build EXIF dictionary
    exif_dict = {
        "Exif": {
            piexif.ExifIFD.ExposureTime: metadata["ExposureTime"],
            piexif.ExifIFD.FNumber: (APERTURE, 10),
            piexif.ExifIFD.ISOSpeedRatings: ISO_SPEED,
            piexif.ExifIFD.ExposureBiasValue: metadata["ExposureBiasValue"],
            piexif.ExifIFD.FocalLength: (FOCAL_LENGTH, 1),
            piexif.ExifIFD.WhiteBalance: WHITEBALANCE, 
        },
        "0th": {
            piexif.ImageIFD.Make: CAMERA_MAKE,
            piexif.ImageIFD.Model: CAMERA_MODEL,  
            piexif.ImageIFD.DateTime: date,
        },
    }

    # Convert EXIF dictionary to bytes
    exif_bytes = piexif.dump(exif_dict)

    # Open the image and save with updated EXIF data
    image = Image.open(f"{IMAGES_FOLDER}/{image_path}")
    image.save(f"{IMAGES_FOLDER}/{image_path}", exif=exif_bytes)


filename_sequence = []

def extract_leading_number(filename):
    match = re.match(r"(\d+)", filename)  # Match leading numbers
    result = int(match.group(1)) if match else float('inf')
    filename_sequence.append(result)
    return result


def sort_all_filenames_in_folder_numerically():
    image_filenames = [
        filename for filename in os.listdir(IMAGES_FOLDER)
        if os.path.isfile(os.path.join(IMAGES_FOLDER, filename)) and any(filename.lower().endswith(ext) for ext in VALID_EXTENSIONS)
    ]
    return sorted(image_filenames, key=extract_leading_number)

def make_sure_all_images_are_present(arr):
    lowest = min(arr)
    highest = max(arr)
    expected_numbers = set(range(lowest, highest + 1))
    missing_numbers = expected_numbers - set(arr)
    if missing_numbers:
        print(f"MISSING FRAME(s) (starts with): {sorted(missing_numbers)}")
        print('Error: Frame(s) missing in the sequence. Please check your IMAGE FOLDER and make sure all frames are present in their correct order.')
        input('Press any key to continue: ')
        return False
    return True


def filter_broken_brackets(filenames, group_size):
    """
    Filters a list of numerically sorted filenames, removing groups where a member is missing.

    Args:
      filenames: A list of filenames, assumed to be numerically sorted.
      group_size: The size of the groups to consider.

    Returns:
      A list of filenames with missing groups removed.
    """
    print("Skipping broken brackets")
    filtered_filenames = []
    start = 0
    while start < len(filenames):
        bracket_start = extract_leading_number(filenames[start])
        bracket_end = bracket_start + group_size - 1 # the number the current bracket should end at
        try:
            file_at_end = extract_leading_number(filenames[start + group_size -1])
        except: # If we have reached the end of the filenames array
            break
        if file_at_end == bracket_end:
            for i in range(start, (start+group_size)):
                filtered_filenames.append(filenames[i])
        else:
            next_supposed_file = bracket_start + group_size
            found = False
            while not found and next_supposed_file < len(filenames):
                for i in range(start, len(filenames)):
                    if extract_leading_number(filenames[i]) == next_supposed_file:
                        start = i
                        found = True
                        break
                next_supposed_file = next_supposed_file + group_size
            continue
        start = start + group_size
    return filtered_filenames


def main():
    print(f"\nProcessing images from Folder: {"Current directory" if IMAGES_FOLDER == '/' else IMAGES_FOLDER}")
    print(f"Image frame pattern is: {FRAME_ORDER}\n")
    frame_number = 0
    bracket_date = None

    sorted_filenames = sort_all_filenames_in_folder_numerically()
    if len(sorted_filenames) == 0:
        print("No image found")
        input("Press Any key to Abort: ")
        return

    proceed = make_sure_all_images_are_present(filename_sequence)
    
    for i in range(0, len(sorted_filenames)):
        filename = sorted_filenames[i]
        if frame_number == 0:
            print('processing', [sorted_filenames[i+j] for j in range(0, FRAME_NUMBER) if i+j < len(sorted_filenames)])
            time.sleep(1)
            bracket_date = datetime.now()
            bracket_date = bracket_date.strftime("%Y:%m:%d %H:%M:%S")
        
        add_exif(filename, FRAME_ORDER[frame_number], bracket_date)
        frame_number += 1
        if frame_number > FRAME_NUMBER - 1:
            frame_number = 0
    print("Completed")

def run():
    proceed = preview_mode()
    if not proceed:
        return
            
    proceed = validate_config_values()
    if proceed:
        main()

if __name__ == '__main__':
    run()