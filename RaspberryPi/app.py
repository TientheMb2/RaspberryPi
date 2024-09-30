from flask import Flask, render_template, request, jsonify
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

app = Flask(__name__)

def validator(instance):
    if not instance.isError():
        decoder = BinaryPayloadDecoder.fromRegisters(
            instance.registers,
            byteorder=Endian.Big,
            wordorder=Endian.Little
        )
        return float(decoder.decode_32bit_float())
    else:
        return None

def read_modbus_data(port, baudrate, timeout, parity, bytesize, unit, address):
    try:
        modbus = ModbusClient(method='rtu', port=port, baudrate=baudrate, timeout=timeout, parity=parity, bytesize=bytesize)
        modbus.connect()
        result = validator(modbus.read_holding_registers(address, 2, unit=unit))
        modbus.close()
        return result
    except Exception as e:
        return str(e)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/read-data', methods=['POST'])
def read_data():
    device = request.form['device']
    data_types = request.form.getlist('data_types')
    addresses = {key: int(request.form[key]) for key in data_types}
    update_interval = int(request.form['update_interval'])

    # Thiết lập thông số mặc định cho PM1200
    if device == "PM1200":
        port = "/dev/ttyUSB0"
        baudrate = 9600
        timeout = 1
        parity = 'E'
        bytesize = 8
        unit = 1
    elif device == "MFM384-C":
        port = "/dev/ttyUSB1"
        baudrate = 19200
        timeout = 2
        parity = 'N'
        bytesize = 8
        unit = 1

    data_results = []
    for data_type in data_types:
        address = addresses[data_type]
        result = read_modbus_data(port, baudrate, timeout, parity, bytesize, unit, address)
        unit_label = ''
        if data_type in ['A1', 'A2', 'A3']:
            unit_label = 'A'
        elif data_type in ['VLL', 'VLN', 'V12', 'V23', 'V31']:
            unit_label = 'V'
        elif data_type in ['PF1', 'PF2', 'PF3']:
            unit_label = ''  # Power factor không có đơn vị
        elif data_type == 'Frequency':
            unit_label = 'Hz'
        
        data_results.append({'type': data_type, 'value': result, 'unit': unit_label})

    return jsonify({'data_results': data_results, 'update_interval': update_interval})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)