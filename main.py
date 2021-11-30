#!venv/bin/python
import serial
import csv
import sys
import glob
from termcolor import colored


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
    with open("res/commands.csv", "r") as file:
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
    ser.timeout = 0.7
    port_num = input("Type port number to connect to: \n")

    ser.port = ports[int(port_num)]
    ser.open()
    if not ser.isOpen():
        print(colored("Error: Port not available or misspelled", "red"))
        startup()
    else:
        return ser


def parse_sw(sw):
    with open("res/SW.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == sw:
                return row[1] + "(" + sw + ")"


def get_SW(resp):
    if len(resp) == 4:
        resp = str(resp)
        return resp[2:-1]
    resp = str(resp)
    return resp[-5:-1]


def parse_resp(resp):
    if len(resp) == 4:
        resp = str(resp)
        return parse_sw(resp[2:-1])

    resp = str(resp)
    sw = resp[-5:-1]
    sw = parse_sw(sw)
    data = resp[2:-5]
    data = str(data)
    data = data.replace("\\x00", '0')
    data = data.replace('\\x01', '1')
    return sw + "::" + data


SW = None


def send_cmd(cmd, ser):
    if cmd[0] == ':':
        print(colored("unknown command", "red"))
        dialog(ser)
    print(colored(">>" + cmd, "blue"))
    ser.write(bytes(cmd, encoding='utf8'))
    resp = ser.read(64)
    print(colored("<<" + parse_resp(resp), "blue"))
    global SW
    SW = get_SW(resp)
    if SW == "9099":
        while not SW == "9000":
            resp = ser.read(64)
            SW = get_SW(resp)

        print(colored("<<" + parse_resp(resp), "blue"))


def run_script(path, ser):
    print("path of script: " + path)
    with open(path, "r") as script:
        lines = script.readlines()
        for line in lines:
            line = line.strip()
            send_cmd(line, ser)


def dialog(ser):
    user_in = input(">>")
    if user_in == ":help":
        print_help(ser)
    elif user_in == ":exit" or user_in == ":e":
        ser.write(b'0399')
        ser.close()
        exit(0)
    elif user_in.startswith(":script"):
        arg = user_in[8:-1]
        run_script(arg, ser)
        dialog(ser)
    else:
        send_cmd(user_in, ser)
        dialog(ser)


def main():
    ser = startup()
    print("Welcome!")
    print("Type command or :help or :exit")
    dialog(ser)


if __name__ == '__main__':
    main()
