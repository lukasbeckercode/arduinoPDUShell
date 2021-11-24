#!venv/bin/python
import serial
import csv
import sys
import glob


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def print_help(ser):
    with open("commands.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            print(row[0] + ": " + row[1])
    print("Full doc: https://lukasbeckercode.github.io/ArduinoPDU/")
    dialog(ser)


def startup():
    i = 0
    ports = serial_ports()
    for port in ports:
        print(str(i) + ": " + port)
        i += 1
    ser = serial.Serial()

    ser.baudrate = 9600
    ser.timeout = 1
    port_num = input("Type port number to connect to: \n")

    ser.port = ports[int(port_num)]
    ser.open()
    if not ser.isOpen():
        print("Error: Port not available or misspelled")
        startup()
    else:
        return ser


def parse_sw(sw):
    with open("SW.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == sw:
                return row[1] + "(" + sw + ")"


def parse_resp(resp):
    if len(resp) == 4:
        resp = str(resp)
        return parse_sw(resp[2:-1])

    resp = str(resp)
    sw = resp[-5:-1]
    sw = parse_sw(sw)
    data = resp[2:-5]
    return sw + "::" + data


def send_cmd(cmd, ser):
    print(">>" + cmd)
    ser.write(bytes(cmd, encoding='utf8'))
    resp = ser.read(64)
    print("<<" + parse_resp(resp))
    dialog(ser)


def dialog(ser):
    user_in = input(">>")
    if user_in == ":help":
        print_help(ser)
    elif user_in == ":exit":
        ser.write(b'0399')
        ser.close()
        exit(0)
    else:
        send_cmd(user_in, ser)


def main():
    ser = startup()
    print("Welcome!")
    print("Type command or :help or :exit")
    dialog(ser)


if __name__ == '__main__':
    main()