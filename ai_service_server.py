from concurrent import futures
import io
import grpc
import ai_service_pb2
import ai_service_pb2_grpc
import time
from faster_whisper import WhisperModel
import pyaudio 
import numpy as np

import logging

class AIServiceServicer(ai_service_pb2_grpc.AIServiceServicer):
    def __init__(self):
        model_size = "tiny"
        logging.info("Loading Whisper model...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logging.info("Whisper model loaded")

    def UploadAudio(self, request, context):
        logging.info("Received UploadAudio request")
        audio_data = io.BytesIO(request.file_data)
        result = self.transcribe_audio(audio_data)
        logging.info("Transcription result: %s", result)
        return ai_service_pb2.TranscriptionResponse(transcription=result)

    def StreamAudio(self, request_iterator, context):
        logging.info("Received StreamAudio request.")
        audio_stream = io.BytesIO()
        buffer_size = 1024  * 15# Example buffer size (10KB)
        buffer = bytearray()

        try:
            for chunk in request_iterator:
                if not chunk.chunk_data:
                    logging.warning("Received empty chunk.")
                    continue
                
                buffer.extend(chunk.chunk_data)

                # If the buffer reaches the defined size, process it
                if len(buffer) >= buffer_size:
                    audio_stream.write(buffer)
                    audio_stream.seek(0)

                    # Save the audio stream to a file for debugging (optional)
                    with open('received_audio.wav', 'wb') as f:
                        f.write(audio_stream.getvalue())

                    try:
                        transcription = self.transcribe_audio(audio_stream)
                        print('chunk:', transcription)
                        logging.info(f"Stream transcription result: {transcription}")
                        yield ai_service_pb2.TranscriptionResponse(transcription=transcription)
                    except Exception as e:
                        logging.error(f"Error during transcription: {e}")
                        yield ai_service_pb2.TranscriptionResponse(transcription="Error during transcription")

                    # Clear the buffer and continue
                    buffer.clear()
                    audio_stream.seek(0, io.SEEK_END)

            # Process any remaining data in the buffer after the stream ends
            if buffer:
                audio_stream.write(buffer)
                audio_stream.seek(0)
                try:
                    transcription = self.transcribe_audio(audio_stream)
                    #print(transcription)
                    yield ai_service_pb2.TranscriptionResponse(transcription=transcription)
                except Exception as e:
                    logging.error(f"Error during transcription of remaining buffer: {e}")
                    yield ai_service_pb2.TranscriptionResponse(transcription="Error during transcription")

        except Exception as e:
            logging.error(f"Error during streaming: {e}")
        finally:
            audio_stream.close()


    def transcribe_audio(self, audio_stream):
        # Ensure the audio_stream is in the correct format for transcription
        try:
            segments, info = self.model.transcribe(audio_stream, beam_size=3)
            transcription = " ".join([segment.text for segment in segments])
            logging.info(f"Transcription: {transcription}")
            return transcription.strip()
        except Exception as e:
            logging.error(f"Error in transcription: {e}")
            return "Error during transcription"

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ai_service_pb2_grpc.add_AIServiceServicer_to_server(AIServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("AI Service Server started.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
