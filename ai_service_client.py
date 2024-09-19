import grpc
import ai_service_pb2
import ai_service_pb2_grpc
import os
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


def upload_file(stub, file_path):
    def file_chunks():
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(1024)  # Read in 1KB chunks
                if not chunk:
                    break
                print(f"Sending chunk of size: {len(chunk)}")
                #return iter([].append(ai_service_pb2.AudioChunk(chunk_data=chunk)))
                yield ai_service_pb2.AudioChunk(chunk_data=chunk)
                
    try:
        response_iterator = stub.StreamAudio(file_chunks())
        for response in response_iterator:
            print(f"Received transcription: {response.transcription}")
    except grpc.RpcError as e:
        print(f"gRPC error: {e.code()} - {e.details()}")
        


def record_and_stream():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, input_device_index=5, frames_per_buffer=CHUNK)
    
    print("Recording...")
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = ai_service_pb2_grpc.AIServiceStub(channel)
        
        def generate_audio_chunks():
            try:
                while True:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    yield ai_service_pb2.AudioChunk(chunk_data=data)
            except KeyboardInterrupt:
                print("Stopped recording")
            finally:
                stream.stop_stream()
                stream.close()
                audio.terminate()
        
        try:
            print("Sending StreamAudio request...")
            responses = stub.StreamAudio(generate_audio_chunks())
            for response in responses:
                print("Transcription:", response.transcription)
        except grpc.RpcError as e:
            print(f"StreamAudio RPC error: {e.code()} - {e.details()}")

def run(audio_file_path):
    # Create a channel and stub for gRPC communication
    channel = grpc.insecure_channel('localhost:50051')
    stub = ai_service_pb2_grpc.AIServiceStub(channel)   
    
    upload_file(stub, audio_file_path)
    
    
     
    # Helper function to read the audio file
    # def read_audio_file(file_path):
    #     if not os.path.exists(file_path):
    #         raise FileNotFoundError(f"Audio file {file_path} not found.")
    #     with open(file_path, 'rb') as f:
    #         return f.read()

    # try:
    #     # Send the audio file to the server
    #     audio_data = read_audio_file(audio_file_path)
    #     print("Sending UploadAudio request...")
    #     response = stub.UploadAudio(ai_service_pb2.AudioFile(file_data=audio_data))
    #     print("Upload Audio Response:", response.transcription)
    # except FileNotFoundError as e:
    #     print(f"Error: {e}")
    # except grpc.RpcError as e:
    #     print(f"Upload Audio RPC error: {e.code()} - {e.details()}")

if __name__ == '__main__':
    run(audio_file_path='audio_test/audio.mp3')
    #record_and_stream()
