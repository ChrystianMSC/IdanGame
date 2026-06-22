import pytest
from unittest.mock import MagicMock, patch, call
import socket
import threading
import time
from src.network.P2PNetworkManager import P2PNetworkManager


@pytest.fixture
def network_manager():
    return P2PNetworkManager()

@patch("socket.socket")
def test_start_as_host_creates_and_binds_socket(mock_socket_class, network_manager):
    """Garante que iniciar como host configura o socket corretamente e dispara a thread de escuta."""
    mock_socket_instance = MagicMock()
    mock_socket_class.return_value = mock_socket_instance

    with patch("threading.Thread") as mock_thread_class:
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        network_manager.start_as_host("127.0.0.1", 8080)

        assert network_manager._is_running is True
        mock_socket_instance.setsockopt.assert_called_once_with(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mock_socket_instance.bind.assert_called_once_with(("127.0.0.1", 8080))
        mock_socket_instance.listen.assert_called_once_with(1)

        # Garante que a thread de escuta foi criada e iniciada
        mock_thread_class.assert_called_once_with(target=network_manager._listen_loop, daemon=True)
        mock_thread_instance.start.assert_called_once()


@patch("socket.socket")
def test_connect_as_guest_success(mock_socket_class, network_manager):
    """Testa o fluxo bem-sucucedido de conexão de um Guest ao Host."""
    mock_socket_instance = MagicMock()
    mock_socket_class.return_value = mock_socket_instance

    with patch.object(network_manager, "_start_receive_loop") as mock_start_loop:
        result = network_manager.connect_as_guest("127.0.0.1", 8080)

        assert result is True
        assert network_manager._is_running is True
        mock_socket_instance.connect.assert_called_once_with(("127.0.0.1", 8080))
        mock_start_loop.assert_called_once()


@patch("socket.socket")
def test_connect_as_guest_failure(mock_socket_class, network_manager):
    """Garante que uma falha de socket na conexão do Guest limpa o estado e retorna False."""
    mock_socket_instance = MagicMock()
    mock_socket_instance.connect.side_effect = socket.error("Erro de conexão")
    mock_socket_class.return_value = mock_socket_instance

    with patch.object(network_manager, "disconnect") as mock_disconnect:
        result = network_manager.connect_as_guest("127.0.0.1", 8080)

        assert result is False
        mock_disconnect.assert_called_once()


def test_listen_loop_accepts_connection(network_manager):
    """Testa o _listen_loop aceitando uma conexão com sucesso e quebrando o laço."""
    network_manager._is_running = True
    mock_server_socket = MagicMock()
    mock_conn_socket = MagicMock()

    # accept() retorna o socket da conexão e o endereço
    mock_server_socket.accept.return_value = (mock_conn_socket, ("127.0.0.1", 54321))
    network_manager._server_socket = mock_server_socket

    with patch.object(network_manager, "_start_receive_loop") as mock_start_loop:
        network_manager._listen_loop()

        mock_server_socket.settimeout.assert_called_once_with(1.0)
        assert network_manager._connection_socket == mock_conn_socket
        mock_start_loop.assert_called_once()


def test_listen_loop_handles_timeout_and_continues(network_manager):
    """Garante que timeouts do accept() mantêm o loop rodando até que o estado mude."""
    network_manager._is_running = True
    mock_server_socket = MagicMock()

    def side_effect_timeout():
        network_manager._is_running = False
        raise socket.timeout()

    mock_server_socket.accept.side_effect = side_effect_timeout
    network_manager._server_socket = mock_server_socket

    with patch.object(network_manager, "_start_receive_loop") as mock_start_loop:
        network_manager._listen_loop()
        mock_start_loop.assert_not_called()


def test_listen_loop_critical_exception_notifies_loss(network_manager):
    """Garante que qualquer exceção grave no accept notifica perda de conexão se ainda rodando."""
    network_manager._is_running = True
    mock_server_socket = MagicMock()
    mock_server_socket.accept.side_effect = Exception("Crash no Driver de Rede")
    network_manager._server_socket = mock_server_socket

    with patch.object(network_manager, "_notify_connection_loss") as mock_notify:
        network_manager._listen_loop()
        mock_notify.assert_called_once()


@patch("src.network.NetworkProtocol.NetworkProtocol.parse_stream")
def test_receive_loop_integration_parses_and_notifies(mock_parse_stream, network_manager):
    """[Integração] Garante que dados crus vindos do socket passam pelo NetworkProtocol e notificam observers."""
    network_manager._is_running = True
    mock_conn = MagicMock()

    def side_effect_recv(buffer_size):
        network_manager._is_running = False  # Para o loop na próxima volta
        return "dados_crus_em_bytes".encode('utf-8')

    mock_conn.recv.side_effect = side_effect_recv
    network_manager._connection_socket = mock_conn

    payload_mockado = {"action": "PING"}
    mock_parse_stream.return_value = ([payload_mockado], "")

    with patch.object(network_manager, "_notify_observers") as mock_notify:
        network_manager._receive_loop()

        mock_parse_stream.assert_called_once_with("dados_crus_em_bytes")
        mock_notify.assert_called_once_with(payload_mockado)


def test_receive_loop_handles_disconnection_packet(network_manager):
    """Garante que pacotes vazios (indicação de socket fechado) disparam perda de conexão."""
    network_manager._is_running = True
    mock_conn = MagicMock()
    mock_conn.recv.return_value = b""
    network_manager._connection_socket = mock_conn

    with patch.object(network_manager, "_notify_connection_loss") as mock_notify:
        network_manager._receive_loop()
        mock_notify.assert_called_once()


@patch("src.network.NetworkProtocol.NetworkProtocol.serialize")
def test_send_success(mock_serialize, network_manager):
    """Testa se a serialização ocorre e os dados reais são transmitidos via sendall."""
    mock_conn = MagicMock()
    network_manager._connection_socket = mock_conn

    payload = {"data": "test"}
    mock_serialize.return_value = b"serialized_payload"

    network_manager.send(payload)

    mock_serialize.assert_called_once_with(payload)
    mock_conn.sendall.assert_called_once_with(b"serialized_payload")


def test_send_no_connection_socket_does_nothing(network_manager):
    """Garante que tentar enviar dados sem conexão estabelecida falha silenciosamente."""
    network_manager._connection_socket = None

    with patch("src.network.NetworkProtocol.NetworkProtocol.serialize") as mock_serialize:
        network_manager.send({"any": "data"})
        mock_serialize.assert_not_called()


@patch("src.network.NetworkProtocol.NetworkProtocol.serialize")
def test_send_socket_error_triggers_loss_notification(mock_serialize, network_manager):
    """Garante que erros inesperados no envio acionam a notificação de desconexão."""
    mock_conn = MagicMock()
    mock_conn.sendall.side_effect = socket.error("Broken pipe")
    network_manager._connection_socket = mock_conn
    mock_serialize.return_value = b"bytes"

    with patch.object(network_manager, "_notify_connection_loss") as mock_notify:
        network_manager.send({"data": 1})
        mock_notify.assert_called_once()


def test_disconnect_full_cleanup(network_manager):
    """Testa o fechamento gracioso e seguro de ambos os sockets ativos (servidor e cliente)."""
    network_manager._is_running = True
    mock_conn = MagicMock()
    mock_server = MagicMock()

    network_manager._connection_socket = mock_conn
    network_manager._server_socket = mock_server

    network_manager.disconnect()

    assert network_manager._is_running is False
    mock_conn.shutdown.assert_called_once_with(socket.SHUT_RDWR)
    mock_conn.close.assert_called_once()
    mock_server.close.assert_called_once()


def test_notify_connection_loss_triggers_callback(network_manager):
    """Garante que todos os observadores escutem o evento de queda de conexão."""
    mock_obs1 = MagicMock()
    mock_obs2 = MagicMock()
    network_manager.register_observer(mock_obs1)
    network_manager.register_observer(mock_obs2)

    network_manager._notify_connection_loss()

    mock_obs1.on_connection_lost.assert_called_once()
    mock_obs2.on_connection_lost.assert_called_once()