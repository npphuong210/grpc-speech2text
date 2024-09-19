from concurrent import futures
import io
import grpc
import ai_service_pb2
import ai_service_pb2_grpc
import time
from faster_whisper import WhisperModel

import logging

class AIServiceServicer(ai_service_pb2_grpc.AIServiceServicer):
    def __init__(self):
        model_size = "medium"
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
        try:
            for chunk in request_iterator:
                if not chunk.chunk_data:
                    logging.warning("Received empty chunk.")
                    continue

                audio_stream.write(chunk.chunk_data)
                audio_stream.seek(0)
                
                # Save the audio stream to a file for debugging
                with open('received_audio.wav', 'wb') as f:
                    f.write(audio_stream.getvalue())
                
                try:
                    result = self.transcribe_audio(audio_stream)
                    logging.info(f"Stream transcription result: {result}")
                    yield ai_service_pb2.TranscriptionResponse(transcription=result)
                except Exception as e:
                    logging.error(f"Error during transcription: {e}")

                audio_stream.seek(0, io.SEEK_END)
        except Exception as e:
            logging.error(f"Error during streaming: {e}")
        finally:
            audio_stream.close()

    def transcribe_audio(self, audio_stream):
        # Ensure the audio_stream is in the correct format for transcription
        audio_stream.seek(0)
        try:
            segments, info = self.model.transcribe(audio_stream, language="id")
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
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
