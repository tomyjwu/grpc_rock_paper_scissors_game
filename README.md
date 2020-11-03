# network_rock_paper_scissors_game
This repository contains complete source codes for a network rock-paper-scissors game. See game session video here: https://youtu.be/-WJN1uhbUhw

To run the application:

1. Make sure you have python installed and setup on your system. App is tested on Python 3.x
2. Download or clone the repository. 
    Recommended virtual env setup `python3 -m venv venv` and `source venv/bin/activate`
3. To start the server: python server.py
4. Click "Start" button on the Server window
5. Lauch two clients. To start a client: python client.py
6. Enter player name and click on "Connect" button

* The game starts when two clients (players) are connected. 
* Enjoy!


# installation
## Windows 10
```
python -m pip install argparse
python -m pip install grpcio
python -m pip install grpcio-tools
python -m pip install protobuf
```

## linux/macos/wsl
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# DevOps
## code gen
```python -m grpc_tools.protoc  -I.  --python_out=.  --grpc_python_out=.  rock_paper_scissors.proto```
