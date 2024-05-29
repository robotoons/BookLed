import serial

# Configure serial connection (if needed, change 'COM4' with correct COM port number)
ser = serial.Serial(
    port='COM4',
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

def read_last_page_number():
    """
    This function reads data from the serial port and extracts the last
    page number from the received data. It handles cases where multiple
    page numbers may be sent in a single read.
    """    
    while True:
         # Read a line from the serial port until a newline character is found       
        line = ser.read_until().decode('utf-8').strip()

        # Remove any carriage return and line feed characters for clean debugging
        clean_line = line.replace('\r', '').replace('\n', '')
        #print(f"Debug: Received line: {clean_line}")  # Debug print without CR or LF

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
                except (ValueError):
                    # Print an error message if conversion fails and continue
                    print("Error: invalid value")  # Error print
                    continue
                    
        # Return the last valid page number found
        if last_page is not None:
            return last_page

try:
    while True:
        # Continuously read and print the current page number
        page_number = read_last_page_number()
        print(f"Current Page: {page_number}")
except KeyboardInterrupt:
    # Handle the interrupt signal to gracefully close the program
    print("Program interrupted")
finally:
    # Ensure the serial port is closed when the program ends
    ser.close()
