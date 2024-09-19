ubuntu:
	sudo apt install portaudio19-dev 
	pip install -r requirements.txt

mac:
	brew install portaudio

proto:
	python3 -m grpc_tools.protoc -I./proto --python_out=. --pyi_out=. --grpc_python_out=. proto/ai_service.proto

.PHONY: ubuntu mac proto