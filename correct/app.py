from flask import Flask, render_template, Response, request, send_from_directory,redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
import os
import face_recognition
import csv
from datetime import datetime
import time
from threading import Thread

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory user storage (for demonstration purposes)
users = {
    '1': {'id': '1', 'username': 'user1', 'email': 'user1@example.com', 'password_hash': generate_password_hash('password1')},
    '2': {'id': '2', 'username': 'user2', 'email': 'user2@example.com', 'password_hash': generate_password_hash('password2')}
}

class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    user_data = users.get(user_id)
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['email'], user_data['password_hash'])
    return None

@app.route('/')
def homepage():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = next((u for u in users.values() if u['email'] == email), None)
        if user:
            print(f"User found: {user}")
            if check_password_hash(user['password_hash'], password):
                login_user(User(user['id'], user['username'], user['email'], user['password_hash']))
                return redirect(url_for('home'))
            else:
                print("Password check failed")
                flash('Invalid email or password')
        else:
            print("User not found")
            flash('Invalid email or password')
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        
        if username:
            user = next((u for u in users.values() if u['username'] == username), None)
            if user:
                flash('A password reset link has been sent to your email')  # For real app, send a reset link
            else:
                flash('Username not found')
        elif email:
            user = next((u for u in users.values() if u['email'] == email), None)
            if user:
                flash('A password reset link has been sent to your email')  # For real app, send a reset link
            else:
                flash('Email not found')
        else:
            flash('Please provide either username or email')
    
    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



path = '/home/raj/Desktop/correct/static/img/S190185'

images = []
classNames = []
myList = os.listdir(path)
print("Image list:", myList)
for idx, cl in enumerate(myList, start=1):
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])

def find_working_camera_index(max_index=10):
    for index in range(max_index):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            cap.release()
            return index
    return None

camera_index = find_working_camera_index()
if camera_index is None:
    print("Error: No working camera found")
    exit()

cap = cv2.VideoCapture(camera_index)
print("Is the camera opened?", cap.isOpened())

if not cap.isOpened():
    print("Error: Could not open video device")
    exit()

encodeListKnown = []
threshold = 0.4

def findEncodings(images):
    encodeList = []
    for img in images:
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(img)
            
            if face_locations:
                encode = face_recognition.face_encodings(img, face_locations)[0]
                encodeList.append(encode)
            else:
                print("No faces found in the image:", img)
        else:
            print("Image is None")
    return encodeList

# Call findEncodings to populate encodeListKnown
encodeListKnown = findEncodings(images)

def recognize_face(img):
    if img is None:
        print("Error: img is None")
        return []

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    recognized_faces = []

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        if len(faceDis) == 0:
            print("No known faces detected")
            name = 'Unknown'
        else:
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex] and faceDis[matchIndex] < threshold:
                name = classNames[matchIndex].upper()
            else:
                name = 'Unknown'

        recognized_faces.append((name, faceLoc))
        print("Recognized faces:", recognized_faces)

    return recognized_faces

@app.route('/caretaker', methods=['POST', 'GET'])
def index():
    return render_template('student_search.html')

@app.route('/caretaker-boys', methods=['POST', 'GET'])
def indexboys():
    return render_template('student_search_boys.html')

@app.route('/main-gate', methods=['POST', 'GET'])
def maingate():
    return render_template('security_maingate.html')

@app.route('/in-out', methods=['POST'])
def index1():
    return render_template('student_search_inout.html')

@app.route('/parent_submit', methods=['POST', 'GET'])
def parentsubmit():
    return render_template('parent_capture.html')

@app.route('/student_check', methods=['POST'])
def student_check():
    student_id = request.form['id']
    found = False
    with open('static/outpass.csv', mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if student_id in row:
                found = True
                break
        
    if found:
        return render_template('index.html')
    else:
        return render_template('no_details.html')
    
@app.route('/student_inout_check', methods=['POST'])
def student_check1():
    student_id = request.form['id']
    found = False
    outtime = None
    intime = None

    with open('static/outpass.csv', mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if student_id in row:
                found = True
                outtime = row[1]  
                intime = row[2]   
                

    if found:
        if outtime.isnumeric() and intime.isnumeric():
            return render_template('no_details.html', message=f'Outpass not issued to {student_id}')
        else:
            return render_template('index_inout.html')
    else:
        return render_template('no_details.html', message='No details are found!')


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        success, img = cap.read()
        print(success)
        if not success:
            print("Error: Failed to capture image")
            return render_template('noface.html')
        
        recognized_faces = recognize_face(img)
        print("Recognized faces in upload:", recognized_faces)
        
        students_path = 'static/student_details.csv'
        details = None
        matched_relation = None
        for i, j in recognized_faces:
            idx = i
            j = j
            with open(students_path, 'r') as file:
                reader = csv.DictReader(file)
                detected = False
                for i in reader:
                    print("Student details:", i)
                    if  i['id'] == idx:
                        details = i
                        matched_relation = i['relation1']
                        detected = True
                        break
                    elif i['id'] == idx:
                        details = i
                        matched_relation = i['relation2']
                        detected = True
                        break
                    elif i['id'] == idx:
                        details = i
                        matched_relation = i['relation3']
                        detected = True
                        break
                    elif i['id'] == idx:
                        details = i
                        matched_relation = i['relation4']
                        detected = True
                        break
                if not detected:
                    return render_template('noface.html')
        return render_template('caretakerissue.html', recognized_faces=recognized_faces, details=details, matched_relation=matched_relation)

@app.route('/upload-boys', methods=['POST'])
def uploadboys():
    if request.method == 'POST':
        success, img = cap.read()
        print(success)
        if not success:
            print("Error: Failed to capture image")
            return render_template('noface.html')
        
        recognized_faces = recognize_face(img)
        print("Recognized faces in upload:", recognized_faces)
        
        students_path = 'static/student_details.csv'
        details = None
        matched_relation = None
        for i, j in recognized_faces:
            idx = i
            j = j
            with open(students_path, 'r') as file:
                reader = csv.DictReader(file)
                detected = False
                for i in reader:
                    print("Student details:", i)
                    if  i['id'] == idx:
                        details = i
                        detected = True
                        break
                if not detected:
                    return render_template('noface.html')
        return render_template('caretakerissue.html', recognized_faces=recognized_faces, details=details)

@app.route('/upload2', methods=['POST'])
def upload2():
    det = None
    outpass_path = 'static/outpass.csv'
    flag = False
    out = False
    in_time = False
    idx = None
    
    if request.method == 'POST':
        success, img = cap.read()
        if not success:
            print("Error: Failed to capture image")
            return render_template('noface.html')
        
        recognized_faces = recognize_face(img)
        print("Recognized faces in upload:", recognized_faces)
        
        students_path = 'static/student_details.csv'
        details = None
        
        for face_id, _ in recognized_faces:
            with open(students_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if (row['relation1'] == str(face_id) or row['id'] == str(face_id) or
                        row['relation2'] == str(face_id) or row['relation3'] == str(face_id) or
                        row['relation4'] == str(face_id)):
                        details = row
                        idx = row['id']
                        break
                
                if details:
                    break

        if not details:
            return render_template('noface.html')
    
    with open(outpass_path, 'r') as file1:
        reader1 = csv.DictReader(file1)
        for i in reader1:
            if i['outpassid'] == idx or i['id'] == idx:
                det = i
                flag = True
                # if det['outtime'] != 'Still in the Campus' and det['intime'] != 'Still in a Leave':
                #     return render_template('failure.html', details=det)

                if det['outtime'] == 'Still in the Campus':
                    out = True

                if det['intime'] == 'Still in a Leave':
                    in_time = True
                # break  # Exit loop once the correct entry is found

        if not flag:
            return render_template('failure.html', idx=idx)

    return render_template('inandout.html', recognized_faces=recognized_faces, details=det, out=out, in_time=in_time)

@app.route('/upload1', methods=['POST'])
def upload1():
    if request.method == 'POST':
        success, img = cap.read()
        print(success)
        if not success:
            print("Error: Failed to capture image")
            return render_template('noface.html')
        
        recognized_faces = recognize_face(img)
        print("Recognized faces in upload:", recognized_faces)
        
        students_path = 'static/student_details.csv'
        details = None
        for i, j in recognized_faces:
            idx = i
            j = j
            with open(students_path, 'r') as file:
                reader = csv.DictReader(file)
                detected = False
                for i in reader:
                    print("Student details:", i)
                    if i['relation1'] == idx or  i['relation2'] == idx or  i['relation3'] == idx or  i['relation4'] == idx:
                        details = i
                        detected = True
                        print("Details:", details)
                if not detected:
                    return render_template('noface.html')
                   
        return render_template('maingateissue.html', recognized_faces=recognized_faces, details=details)

    
@app.route('/idnumber', methods=['POST'])
def idnum():
    idx = request.form.get('id')
    students_path = 'static/student_details.csv'
    details = None
    with open(students_path, 'r') as file1:
        reader1 = csv.DictReader(file1)
        for i in reader1:
            if i['id'] == idx:
                details = i
    if details is None:
        return render_template('noface.html')  # or handle as per your application logic

    return render_template('success.html', details=details)


@app.route('/fetch', methods=['POST'])
def fetch():
    det = None
    idx = request.form.get('id')
    outpass_path = 'static/outpass.csv'
    flag = False
    out = False
    in_time = False
    with open(outpass_path, 'r') as file1:
        reader1 = csv.DictReader(file1)
        for i in reader1:
            if i['outpassid'] == idx or i['id'] == idx:
                det = i
                flag = True
                if det['outtime'] != 'Still in the Campus' and det['intime'] != 'Still in a Leave':
                    return render_template('failure.html', details=det)

                if det['outtime'] == 'Still in the Campus':
                    out = True

                if det['intime'] == 'Still in a Leave':
                    in_time = True
        if not flag:
            return render_template('failure.html', idx=idx)
    return render_template('inandout.html', details=det, out=out, in_time=in_time)

def generate_unique_id(student_id):
    timestamp = int(time.time())
    unique_id = f"SKLM{timestamp}"
    return unique_id

outpass_path = 'static/outpass.csv'
outpass_path = '/home/raj/Desktop/correct/static/outpass.csv'

@app.route('/detail1', methods=['POST'])
def detail1():
    reason = False
    idx = request.form.get('id')
    name = request.form.get('name')
    branch = request.form.get('branch')
    year = request.form.get('year')
    issue_time = False
    date = False
    outtime = 'Still in the Campus'
    intime = '-'
    outpassid = False

    # Writing to the outpass file
    with open(outpass_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([idx, name, branch, year, issue_time, outtime, date, reason, intime, outpassid])

    # Reading from the outpass file
    with open(outpass_path, 'r', newline='') as file:
        reader = csv.reader(file)
        issued_outpasses = list(reader)  # Convert the reader to a list

    return render_template('success.html', issued_outpasses=issued_outpasses, outpassid=outpassid)

@app.route('/detail2', methods=['POST'])
def detail2():
    reason = request.form.get('reason')
    idx = request.form.get('id')
    name = request.form.get('name')
    branch = request.form.get('branch')
    year = request.form.get('year')
    issue_time = str(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
    date = str(datetime.now().date())
    outtime_new = 'Still in the Campus'  # Default value for new outpass
    intime_new = '-'  # Default value for new outpass
    outpassid = generate_unique_id(idx)

    outpass_path = 'static/outpass.csv'
    rows = []
    fieldnames = ['id', 'name', 'branch', 'year', 'issued_time', 'outtime', 'date', 'reason', 'intime', 'outpassid']
    new_entry_needed = True

    # Ensure the file exists before attempting to read it
    if os.path.exists(outpass_path):
        with open(outpass_path, 'r', newline='') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames

            # Check if the student has completed their previous outpass
            for row in reader:
                if row['id'] == idx and (row['outtime'] != 'Still in the Campus' or row['intime'] != '-'):
                    # Preserve existing record for the student if previous outpass is completed
                    # return render_template('failure.html', idx=idx, message="You have not completed your current outpass process.", not_completed=True, not_issued=False)
                    rows.append(row)
                else:
                    # Check if the outpassid or issue_time is 'False' and if so, update the row
                    if row['id'] == idx and (row['outpassid'] == 'False' or row['issued_time'] == 'False'):
                        row['issued_time'] = issue_time
                        row['outpassid'] = outpassid
                        row['reason'] = reason
                        new_entry_needed = False
                    rows.append(row)

    # Add new record for the new outpass only if no row needs update
    if new_entry_needed:
        new_row = {
            'id': idx,
            'name': name,
            'branch': branch,
            'year': year,
            'issued_time': issue_time,
            'outtime': outtime_new,
            'date': date,
            'reason': reason,
            'intime': intime_new,
            'outpassid': outpassid
        }
        rows.append(new_row)

    # Write all rows back to the file
    with open(outpass_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Reading from the file to pass to the template
    with open(outpass_path, 'r', newline='') as file:
        reader = csv.reader(file)
        issued_outpasses = list(reader)  # Convert the reader to a list

    return render_template('success.html', issued_outpasses=issued_outpasses, outpassid=outpassid)

@app.route('/security', methods=['POST', 'GET'])
def security():
    idx = request.form.get('id')
    status = request.form.get('status')

    if not idx or not status:
        return render_template('failure.html', message="ID or status missing")

    outpass_path = 'static/outpass.csv'
    rows = []

    if status == '1':  # Leaving
        outtime = str(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
        with open(outpass_path, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 9:
                    print("Row does not have enough columns:", row)
                    continue
                if row[0] == idx:
                    print("Outpass details:", row)
                    if row[5] == 'Still in the Campus' and row[8] == '-':  # Check if leaving and entering are empty
                        row[5] = outtime
                        row[8] = 'Still in a Leave'
                rows.append(row)

    elif status == '2':  # Entering
        intime = str(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
        with open(outpass_path, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 9:
                    print("Row does not have enough columns:", row)
                    continue
                if row[0] == idx:
                    print("Outpass details:", row)
                    if row[5] != '' and row[8] == 'Still in a Leave':  # Check if leaving is filled but entering is empty
                        row[8] = intime
                rows.append(row)

    else:
        print('Invalid status')
        return render_template('failure.html', message="Invalid status")

    with open(outpass_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    return render_template('success.html', issued_outpasses=rows, status=status)


@app.route('/download_csv')
def download_csv():
    directory = 'static'
    filename = 'outpass.csv'
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():
    while True:
        success, frame = cap.read()
        print(success)
        if not success:
            print("Failed to read frame from camera")
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Failed to encode frame")
            break

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def run_flask():
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    flask_thread.start()