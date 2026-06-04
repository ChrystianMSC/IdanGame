from abc import ABC, abstractmethod

class NetworkObserver(ABC):

    @abstractmethod
    def on_message_received(self, data):
        pass

    @abstractmethod
    def on_connection_lost(self):
        pass