import json

class NetworkProtocol:

    @staticmethod
    def serialize(data):
        message_str = json.dumps(data) + "\n"
        return message_str.encode('utf-8')

    @staticmethod
    def parse_stream(buffer):
        payloads = []
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if line.strip():
                try:
                    payloads.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return payloads, buffer