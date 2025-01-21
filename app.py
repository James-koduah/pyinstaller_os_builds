import re
import sys
import piexif
from PIL import Image
import os
from datetime import datetime
import time
from dotenv import load_dotenv
load_dotenv()


IMAGES_FOLDER = os.getenv("IMAGES_FOLDER")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER")
OUTPUT_LOG_FILE = os.getenv("OUTPUT_LOG_FILE")
PREVIEW_MODE = os.getenv("PREVIEW_MODE", 'true').lower() in ("true", "1", "yes")
SUPRESS_ERRORS = os.getenv("SUPRESS_ERRORS", 'False').lower() in ("true", "1", "yes")
CAMERA_MAKE = os.getenv("CAMERA_MAKE", "Unknown Camera Make")
CAMERA_MODEL = os.getenv("CAMERA_MODEL", "Unknown Camera Model")
WHITEBALANCE = os.getenv("WHITEBALANCE", 0)
FOCAL_LENGTH = os.getenv("FOCAL_LENGTH", 50)
ISO_SPEED = os.getenv("ISO_SPEED", 100)
APERTURE = os.getenv("APERTURE", 28)

FRAME_ORDER = os.getenv("FRAME_ORDER", "under,over,normal")
FRAME_ORDER = FRAME_ORDER.split(',')
VALID_EXTENSIONS = os.getenv("VALID_EXTENSIONS", ".jpg,.png,.tiff,.tif")
VALID_EXTENSIONS = VALID_EXTENSIONS.split(',')

UNDER_EXPOSURE_TIME = os.getenv("UNDER_EXPOSURE_TIME", 500)
UNDER_EXPOSURE_BIAS = os.getenv("UNDER_EXPOSURE_BIAS", -2)

NORMAL_EXPOSURE_TIME = os.getenv("NORMAL_EXPOSURE_TIME", 100)
NORMAL_EXPOSURE_BIAS = os.getenv("NORMAL_EXPOSURE_BIAS", 0)

OVER_EXPOSURE_TIME = os.getenv("OVER_EXPOSURE_TIME", 50)
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
NORMAL_EXPOSURE_TIME = convert_to_int("NORMAL_EXPOSURE_TIME", NORMAL_EXPOSURE_TIME)
NORMAL_EXPOSURE_BIAS = convert_to_int("NORMAL_EXPOSURE_BIAS", NORMAL_EXPOSURE_BIAS)
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

    print('--------- NORMAL FRAME ----------')
    print(f'Exposure Time: 1/{NORMAL_EXPOSURE_TIME}\nExposure Bias: {NORMAL_EXPOSURE_BIAS} EV')

    print('--------- OVER FRAME ----------')
    print(f'Exposure Time: 1/{OVER_EXPOSURE_TIME}\nExposure Bias: {OVER_EXPOSURE_BIAS} EV')
    
    print("Are you okay with these changes?")
    answer = input("Continue processing? (yes/no): ")
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
    
    if not OUTPUT_FOLDER:
        print("Caution: No output folder specified. The original image will be edited.")
        answer = input("Continue processing? (yes/no): ")
        if answer.lower() != 'yes' and answer.lower() != 'y':
            print('Aborting...')
            return False
    return True


hdr_metadata = {
    "under": {
        "ExposureTime": (1, UNDER_EXPOSURE_TIME),       # Exposure time: 1/200s
        "FNumber": (APERTURE, 10),           # Aperture: f/2.8
        "ISOSpeedRatings": ISO_SPEED,        # ISO 100
        "ExposureBiasValue": (UNDER_EXPOSURE_BIAS, 1),  # Exposure bias: -2 EV
    },
    "normal": {
        "ExposureTime": (1, NORMAL_EXPOSURE_TIME),      # Exposure time: 1/100s
        "FNumber": (APERTURE, 10),           # Aperture: f/2.8
        "ISOSpeedRatings": ISO_SPEED,        # ISO 100
        "ExposureBiasValue": (NORMAL_EXPOSURE_BIAS, 1),   # Exposure bias: 0 EV
    },
    "over": {
        "ExposureTime": (1, OVER_EXPOSURE_TIME),       # Exposure time: 1/50s
        "FNumber": (APERTURE, 10),           # Aperture: f/2.8
        "ISOSpeedRatings": ISO_SPEED,        # ISO 100
        "ExposureBiasValue": (OVER_EXPOSURE_BIAS, 1),   # Exposure bias: +2 EV
    },
}


def add_exif(image_path, type, date):
    metadata = hdr_metadata.get(type)
    if not metadata:
        return
    
    # Build EXIF dictionary
    exif_dict = {
        "Exif": {
            piexif.ExifIFD.ExposureTime: metadata["ExposureTime"],
            piexif.ExifIFD.FNumber: metadata["FNumber"],
            piexif.ExifIFD.ISOSpeedRatings: metadata["ISOSpeedRatings"],
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
    if OUTPUT_FOLDER:
        try:
            image.save(f"{OUTPUT_FOLDER}/{image_path}", exif=exif_bytes)
        except Exception as e:
            print("Output Folder does not exist. Please create it.")
            sys.exit()
    else:
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

def main():
    print(f"\nProcessing images from Folder: {IMAGES_FOLDER}")
    print(f"Image frame pattern is: {FRAME_ORDER}\n")
    frame_number = 0
    bracket_date = None

    sorted_filenames = sort_all_filenames_in_folder_numerically()
    proceed = make_sure_all_images_are_present(filename_sequence)
    if not proceed and not SUPRESS_ERRORS:
        print("To suppress this error and proceed, set SUPRESS_ERRORS in the config file to true\n")
        input("Press Any key to Abort: ")
        return
    
    for i in range(0, len(sorted_filenames)):
        filename = sorted_filenames[i]
        if any(filename.lower().endswith(ext) for ext in VALID_EXTENSIONS):
            if frame_number == 0:
                print(f"Processing frame group ({sorted_filenames[i], sorted_filenames[i+1], sorted_filenames[i+2]})")
                time.sleep(2)
                bracket_date = datetime.now()
                bracket_date = bracket_date.strftime("%Y:%m:%d %H:%M:%S")
            
            add_exif(filename, FRAME_ORDER[frame_number], bracket_date)
            frame_number += 1
            if frame_number > 2:
                frame_number = 0

def run():
    if PREVIEW_MODE:
        proceed = preview_mode()
        if not proceed:
            return
            
    proceed = validate_config_values()
    if proceed:
        main()

if __name__ == '__main__':
    run()