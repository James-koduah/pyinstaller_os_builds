import re
import piexif
from PIL import Image
import os


def add_exif(folder_path, image_path, metadata, frame_data, date, output_folder=False):
    
    # Build EXIF dictionary
    exif_dict = {
        "Exif": {
            piexif.ExifIFD.ExposureTime: (1, frame_data.get('exposure_time')),
            piexif.ExifIFD.FNumber: (metadata.get('aperture'), 10),
            piexif.ExifIFD.ISOSpeedRatings: metadata.get('iso_speed'),
            piexif.ExifIFD.ExposureBiasValue: (frame_data.get('exposure_bias'), 1),
            piexif.ExifIFD.FocalLength: (metadata.get('focal_length'), 1),
            piexif.ExifIFD.WhiteBalance: metadata.get('white_balance'), 
        },
        "0th": {
            piexif.ImageIFD.Make: metadata.get('camera_make'),
            piexif.ImageIFD.Model: metadata.get('camera_model'),  
            piexif.ImageIFD.DateTime: date,
        },
    }

    # Convert EXIF dictionary to bytes
    exif_bytes = piexif.dump(exif_dict)

    # Open the image and save with updated EXIF data
    image = Image.open(f"{folder_path}/{image_path}")
    if output_folder:
        try:
            image.save(f"{output_folder}/{image_path}", exif=exif_bytes)
        except Exception as e:
            pass
    else:
        image.save(f"{folder_path}/{image_path}", exif=exif_bytes)


# filename_sequence = []

def extract_leading_number(filename):
    match = re.match(r"(\d+)", filename)  # Match leading numbers
    result = int(match.group(1)) if match else float('inf')
    return result


def sort_all_filenames_in_folder_numerically(images_folder):
    image_filenames = [
        filename for filename in os.listdir(images_folder)
        if os.path.isfile(os.path.join(images_folder, filename)) and any(filename.lower().endswith(ext) for ext in ['.jpg', '.tif', '.tiff', '.png', '.jpeg', '.dng', '.cr2', '.nef', '.arw'])
    ]
    return sorted(image_filenames, key=extract_leading_number)

def filter_broken_brackets(filenames, group_size):
    """
    Filters a list of numerically sorted filenames, removing groups where a member is missing.

    Args:
      filenames: A list of filenames, assumed to be numerically sorted.
      group_size: The size of the groups to consider.

    Returns:
      A list of filenames with missing groups removed.
    """

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

def make_sure_all_images_are_present(raw_arr):
    arr = []
    for i in raw_arr:
        arr.append(extract_leading_number(i))
    lowest = min(arr)
    highest = max(arr)
    expected_numbers = set(range(lowest, highest + 1))
    missing_numbers = expected_numbers - set(arr)
    if missing_numbers:
        return list(missing_numbers)
    return False
