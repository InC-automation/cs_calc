import grpc
import elecont_pb2, elecont_pb2_grpc
import time
from аrithmetics import аrithmetic

calculation = аrithmetic()

try:            
    while True:
        calculation.read_data()
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    print("Finish...")



  
#raise SystemExit 
