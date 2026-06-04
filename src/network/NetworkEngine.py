from abc import ABC, abstractmethod

class NetworkEngine(ABC):

    @abstractmethod
    def start_as_host(self, host, port):
        pass

    @abstractmethod
    def connect_as_guest(self, host, port):
        pass

    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def disconnect(self):
        pass