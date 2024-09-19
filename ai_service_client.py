import grpc
import ai_service_pb2
import ai_service_pb2_grpc
import os
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

def record_and_stream():
    if input("Do you want to upload an audio file? (y/n): ").lower() != 'y':
            raise FileNotFoundError("No audio file selected.")
    else:
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

def run():
    # Create a channel and stub for gRPC communication
    channel = grpc.insecure_channel('localhost:50051')
    stub = ai_service_pb2_grpc.AIServiceStub(channel)

    audio_file_path = 'audio.mp3'
    
    # Helper function to read the audio file
    def read_audio_file(file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file {file_path} not found.")
        with open(file_path, 'rb') as f:
            return f.read()

    try:
        if input("Do you want to upload an audio file? (y/n): ").lower() != 'y':
            raise FileNotFoundError("No audio file selected.")
        else:
            audio_data = read_audio_file(audio_file_path)
            print("Sending UploadAudio request...")
            response = stub.UploadAudio(ai_service_pb2.AudioFile(file_data=audio_data))
            print("Upload Audio Response:", response.transcription)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except grpc.RpcError as e:
        print(f"Upload Audio RPC error: {e.code()} - {e.details()}")

if __name__ == '__main__':
    run()
    record_and_stream()
