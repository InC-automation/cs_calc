import grpc
import elecont_pb2, elecont_pb2_grpc
from datetime import datetime, timezone, timedelta
import time
import configparser

class аrithmetic:  

    grcp_connect_status = False
    grpc_channel = grpc.insecure_channel('localhost:29041')
    cycle_period = 10
    trace = True
    x_dict = {}
    x_values = {}
    y_dict = {}
    y_signals = {}
    stub = elecont_pb2_grpc.ElecontStub(grpc_channel)

    def __init__(self): # Прочитать настройки из файла setting.ini
        config = configparser.ConfigParser()
        config.read('settings.ini')
        self.grpc_url = config['Default']['ELECONT_GRPC']
        self.cycle_period = float(config['Default']['CALC_PERIOD'])/1000
        self.trace = bool(int(config['Default']['TRACE']))
        self.time_delta = int(config['Default']['TIME_DELTA'])
        self.grpc_channel = grpc.insecure_channel(self.grpc_url)
        self.stub = elecont_pb2_grpc.ElecontStub(self.grpc_channel)

    def grcp_connect(self):  # установка соединения и чтение сигналов
        if self.grcp_connect_status: return
        
        print(f'{datetime.now().time()} gRPC connect ({self.grpc_url})...')   
        
        try:
            cs_data = self.stub.GetAllObjectsData(elecont_pb2.Empty())
        except grpc.RpcError as e:
            print(f'{datetime.now().time()} gRPC connect error: {e.code()}, {e.details()}')            
            self.grcp_connect_status = False
            time.sleep(5)
        else:
            print(f'{datetime.now().time()} gRPC connect SUCCESS')
            self.grcp_connect_status = True
            self.x_dict.clear()
            self.x_values.clear()
            self.y_dict.clear()
            self.y_signals.clear()

            for obj in cs_data.data:
                if elecont_pb2.ObjectFamily.Value.Name(obj.family.value) == 'RX_SIGNAL':
                    self.y_dict[obj.guid] = obj.userdata
                    self.y_signals[obj.guid] = self.stub.GetSignalByGuid(elecont_pb2.Guid(guid = obj.guid))
                elif elecont_pb2.ObjectFamily.Value.Name(obj.family.value) == 'TX_SIGNAL':
                    self.x_dict[obj.guid] = obj.userdata
                    #x_values[obj.userdata] = Stub.GetSignalByGuid(elecont_pb2.Guid(guid = obj.guid)).value
       
    def read_data(self):
        if not self.grcp_connect_status: 
            self.grcp_connect()
            time.sleep(1)
        else:
            if self.trace: print(f'{datetime.now().time()} read_data...')
            for item in self.x_dict:
                try:
                    x_signal = self.stub.GetSignalByGuid(elecont_pb2.Guid(guid = item))
                except grpc.RpcError as e:
                    print(f'{datetime.now().time()} GetSignalByGuid: gRPC error: {e.code()}, {e.details()}')
                    self.grcp_close(1)
                else:
                    if(x_signal.value) == '': continue
                    self.x_values[self.x_dict[item]] = float(x_signal.value)
            self.calc_data()

    def calc_data(self):
        if not self.grcp_connect_status: 
            self.grcp_connect()
            time.sleep(1)
        else:
            if self.trace: print(f'{datetime.now().time()} calc...')            
            for item in self.y_dict:
                new_value = eval(self.y_dict[item], self.x_values)
                y_signal = self.stub.GetSignalByGuid(elecont_pb2.Guid(guid = item))
                if str(new_value) != y_signal.value:          
                    y_signal.time = self.get_timestamp()
                    y_signal.value = str(new_value)
                    y_signal.quality = 0
                    self.y_signals[item] = y_signal
                    try:
                        self.stub.SetSignal(y_signal)
                    except grpc.RpcError as e:
                        print(f'{datetime.now().time()} SetSignal: gRPC error: {e.code()}, {e.details()}')
                        self.grcp_close(1)
                        return
            time.sleep(self.cycle_period)
        
    # метод возвращает текущее время в формате КС
    def get_timestamp(self):  
        tz = timezone(timedelta(hours=self.time_delta))
        time_now = datetime.now().replace(tzinfo = tz)
        timestamp = int(time_now.timestamp() * 1000)
        return timestamp
        
    def grcp_close(self, tSleep = 0):
        print(f'{datetime.now().time()} Close gRPC connect...')
        self.grcp_connect_status = False
        #try:
        #    self.grpc_channel.close()
        #except:
        #    pass
        time.sleep(tSleep)
        
    # финализация класса
    def __del__(self): 
        print(f'{datetime.now().time()} Close gRPC connect (final)...')
        try:
            self.grpc_channel.close()
        except:
            pass