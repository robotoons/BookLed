import os
import serial
import threading
import requests
from pydub import AudioSegment
import wave
import pyaudio

# Configure the serial connection (modify 'COM4' with the correct COM port)
ser = serial.Serial(
    port='COM4',
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

current_page = None
stop_audio = False

# Create a temporary directory to save downloaded MP3 files
temp_dir = "temp_mp3"
os.makedirs(temp_dir, exist_ok=True)

def download_mp3(url, filename):
    print(f"Downloading MP3 from {url}")
    response = requests.get(url)
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded MP3 to {file_path}")
    return file_path

def read_last_page_number():
    """
    This function reads data from the serial port and extracts the last
    page number from the received data. It handles cases where multiple
    page numbers may be sent in a single read.
    """    
    while True:
        # Read a line from the serial port until a newline character is found
        line = ser.read_until().decode('utf-8').strip()
        print(f"Read line from serial: {line}")

        # Remove any carriage return and line feed characters for clean debugging
        clean_line = line.replace('\r', '').replace('\n', '')
        
        # Split the cleaned line by the delimiter 'P:' to find all page codes
        pages = clean_line.split('P:')
        last_page = None

        # Iterate through the list of possible page codes
        for page in pages:
            if page:
                try:
                    # Strip any extra whitespace and convert the hex value to decimal
                    page_number_hex = page.strip()
                    page_number_dec = int(page_number_hex, 16)
                    # Update the last_page with the most recent valid page number
                    last_page = page_number_dec
                    print(f"Extracted page number: {last_page}")
                except (ValueError):
                    # Print an error message if conversion fails and continue
                    print("Error: invalid value")
                    continue
                    
        # Return the last valid page number found
        if last_page is not None:
            return last_page

def play_audio(file_path):
    global stop_audio
    stop_audio = False
    print(f"Starting playback of {file_path}")
    
    # Convert MP3 to WAV
    audio = AudioSegment.from_mp3(file_path)
    audio.export("temp.wav", format="wav")
    print(f"Converted MP3 to WAV for {file_path}")

    # Open the WAV file
    wf = wave.open("temp.wav", 'rb')

    # Create a PyAudio instance
    p = pyaudio.PyAudio()

    # Open a stream
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Read the data
    data = wf.readframes(1024)

    # Play the stream
    while data and not stop_audio:
        stream.write(data)
        data = wf.readframes(1024)

    # Stop the stream
    stream.stop_stream()
    stream.close()

    # Close PyAudio and the WAV file
    p.terminate()
    wf.close()
    os.remove("temp.wav")
    print(f"Playback finished for {file_path}")

def play_mp3_in_thread(file_path):
    thread = threading.Thread(target=play_audio, args=(file_path,))
    thread.start()
    return thread

# Map page numbers to MP3 files
page_to_mp3 = {
    1: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/01_tav_audio_eng.mp3?raw=true",
    2: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/02_tav_audio_eng.mp3?raw=true",
    3: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/03_tav_audio_eng.mp3?raw=true",
    4: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/04_tav_audio_eng.mp3?raw=true",
    5: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/05_tav_audio_eng.mp3?raw=true",    
    6: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/06_tav_audio_eng.mp3?raw=true",
    7: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/07_tav_audio_eng.mp3?raw=true",
    8: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/08_tav_audio_eng.mp3?raw=true",    
    9: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/09_tav_audio_eng.mp3?raw=true",
    10: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/10_tav_audio_eng.mp3?raw=true",    
    11: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/11_tav_audio_eng.mp3?raw=true",    
    12: "https://github.com/robotoons/BookLed/blob/main/contents/Gu-File_%2301/mp3/ENG/12b_tav_audio_eng.mp3?raw=true",
}

audio_thread = None

try:
    while True:
        page_number = read_last_page_number()
        if page_number != current_page:
            current_page = page_number
            print(f"Current Page: {current_page}")

            if current_page in page_to_mp3:
                # Stop current audio
                stop_audio = True
                if audio_thread is not None:
                    audio_thread.join()

                # Download the new MP3 file
                mp3_url = page_to_mp3[current_page]
                mp3_filename = f"page_{current_page}.mp3"
                mp3_path = download_mp3(mp3_url, mp3_filename)
                
                # Play the new MP3 file
                audio_thread = play_mp3_in_thread(mp3_path)
except KeyboardInterrupt:
    # Handle the interrupt signal to gracefully close the program
    print("Program interrupted")
finally:
    # Ensure the serial port is closed when the program ends
    ser.close()
    stop_audio = True
    if audio_thread is not None:
        audio_thread.join()
    print("Program terminated")
