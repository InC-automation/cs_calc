import grpc
import elecont_pb2, elecont_pb2_grpc
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
