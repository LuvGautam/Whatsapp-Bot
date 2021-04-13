import face_recognition
from pathlib import Path

def add_user_by_face(unknown_img_path):
    # Load the jpg files into numpy arrays
    known_faces_path = Path('profile_pictures')

    known_images = {}
##    for file in known_faces_path.iterdir():
##        if file.is_file():
##            known_images[file.stem] = {'image': face_recognition.load_image_file(file), 'encoding': None}
    file = known_faces_path.joinpath(fr'{unknown_img_path.parts[-2]}.jpg')

    if not file.is_file():
        return None, 'Unable to find profile picture'
    
    known_images[unknown_img_path.parts[-2]] = {'image': face_recognition.load_image_file(file), 'encoding': None}

    unknown_image = face_recognition.load_image_file(unknown_img_path)
    unknown_image_encoding = face_recognition.face_encodings(unknown_image)

    # Get the face encodings for each face in each image file
    # Since there could be more than one face in each image, it returns a list of encodings.
    # But since I know each image only has one face, I only care about the first encoding in each image, so I grab index 0.

    for known in known_images:
        known_images[known]['encoding'] = face_recognition.face_encodings(known_images[known]['image'])

    for unknown in unknown_image_encoding:
        for known in known_images:
            results = face_recognition.compare_faces(known_images[known]['encoding'], unknown, tolerance=0.50)
            if True in results:
                return known, 'success'

    return None, 'Unable to recognize face'

if __name__ == '__main__':
    user, log = add_user_by_face(Path(r'C:\Users\LUV\Desktop\image\pp (3).jpg'))
    print(user, log)
    
