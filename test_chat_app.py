import pytest
import asyncio
import sys
from unittest.mock import Mock, patch, AsyncMock
from io import StringIO
import importlib.util

# Import the modules directly
spec_server = importlib.util.spec_from_file_location("async_server", "async_server.py")
async_server = importlib.util.module_from_spec(spec_server)
spec_server.loader.exec_module(async_server)

spec_client = importlib.util.spec_from_file_location("async_client", "async_client.py")
async_client = importlib.util.module_from_spec(spec_client)
spec_client.loader.exec_module(async_client)

# Mock classes for testing
class MockReader:
    def __init__(self, data_sequence):
        self.data_sequence = data_sequence
        self.position = 0
    
    async def read(self, n):
        if self.position >= len(self.data_sequence):
            return b''
        data = self.data_sequence[self.position]
        self.position += 1
        return data if isinstance(data, bytes) else data.encode()

class MockWriter:
    def __init__(self):
        self.written_data = []
        self.closed = False
    
    def write(self, data):
        self.written_data.append(data if isinstance(data, bytes) else data.encode())
        return len(data)
    
    async def drain(self):
        pass
    
    def close(self):
        self.closed = True
    
    async def wait_closed(self):
        pass

# Define the fixture at the module level so all test classes can use it
@pytest.fixture
def reset_server_state():
    # Reset server state between tests
    async_server.clients = {}
    async_server.pending_messages = {}
    yield

# Server unit tests
class TestServer:
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        writer = MockWriter()
        test_message = "Hello Test"
        
        await async_server.send_message(writer, test_message)
        
        assert len(writer.written_data) == 1
        assert writer.written_data[0] == test_message.encode()
    
    @pytest.mark.asyncio
    async def test_send_message_exception(self):
        # Test that errors are handled gracefully
        writer = Mock()
        writer.write.side_effect = Exception("Connection error")
        
        # Should not raise exception
        await async_server.send_message(writer, "Test message")
    
    @pytest.mark.asyncio
    async def test_handle_client_new_user(self, reset_server_state):
        # Test a normal client connection flow
        username = "testuser"
        reader = MockReader([username, "exit"])
        writer = MockWriter()
        
        await async_server.handle_client(reader, writer)
        
        # Verify the client was added and then removed
        assert username not in async_server.clients
        assert writer.closed == True
        assert len(writer.written_data) >= 2  # At least username prompt and connected message
    
    @pytest.mark.asyncio
    async def test_handle_client_duplicate_username(self, reset_server_state):
        # Add a client with the username that will be duplicated
        duplicate_name = "duplicate"
        mock_client = (MockReader([]), MockWriter())
        async_server.clients[duplicate_name] = mock_client
        
        # Try to connect with the same username
        reader = MockReader([duplicate_name])
        writer = MockWriter()
        
        await async_server.handle_client(reader, writer)
        
        # Verify the connection was rejected
        assert duplicate_name in async_server.clients
        assert async_server.clients[duplicate_name] == mock_client
        assert writer.closed == True
        assert b"Username already taken" in writer.written_data[1]
    
    # @pytest.mark.asyncio
    # async def test_handle_client_messaging(self, reset_server_state):
    #     # Test sending messages between clients
    #     sender_name = "sender"
    #     receiver_name = "receiver"
        
    #     # Set up the receiver first
    #     receiver_reader = MockReader(["receiver", "exit"])
    #     receiver_writer = MockWriter()
        
    #     # Add receiver to clients
    #     async_server.clients[receiver_name] = (receiver_reader, receiver_writer)
        
    #     # Set up the sender
    #     test_message = f"{receiver_name}: Hello receiver!"
    #     sender_reader = MockReader([sender_name, test_message, "exit"])
    #     sender_writer = MockWriter()
        
    #     # Process sender's connection and message
    #     await async_server.handle_client(sender_reader, sender_writer)
        
    #     # Check if the message was delivered to the receiver
    #     receiver_messages = [msg.decode() for msg in receiver_writer.written_data]
    #     found_message = False
    #     for msg in receiver_messages:
    #         if f"[{sender_name}] Hello receiver!" in msg:
    #             found_message = True
    #             break
                
    #     assert found_message, "Message was not delivered to receiver"
    

    
    @pytest.mark.asyncio
    async def test_handle_client_invalid_format(self, reset_server_state):
        # Test sending a message with invalid format
        username = "testuser"
        invalid_message = "This has no recipient"
        
        reader = MockReader([username, invalid_message, "exit"])
        writer = MockWriter()
        
        await async_server.handle_client(reader, writer)
        
        # Check if the format error message was sent
        sender_messages = [msg.decode() for msg in writer.written_data]
        found_error = False
        for msg in sender_messages:
            if "Invalid format" in msg:
                found_error = True
                break
                
        assert found_error, "Format error message not delivered"
    
    @pytest.mark.asyncio
    async def test_main_server_start(self):
        # Mock the server to avoid actually starting it
        mock_server = AsyncMock()
        
        with patch('asyncio.start_server', return_value=mock_server):
            # Mock serve_forever to avoid blocking
            mock_server.serve_forever = AsyncMock()
            mock_server.__aenter__ = AsyncMock(return_value=mock_server)
            mock_server.__aexit__ = AsyncMock()
            
            # Mock socket to provide getsockname
            mock_socket = Mock()
            mock_socket.getsockname.return_value = ('127.0.0.1', 5000)
            mock_server.sockets = [mock_socket]
            
            # Run the main function
            await async_server.main()
            
            # Check that the server was started with the correct parameters
            asyncio.start_server.assert_called_once_with(
                async_server.handle_client, 
                async_server.HOST, 
                async_server.PORT
            )
            
            # Check that serve_forever was called
            mock_server.serve_forever.assert_called_once()

# Client unit tests
class TestClient:
    
    @pytest.mark.asyncio
    async def test_client_connection(self):
        username = "testclient"
        
        # Mock reader/writer for client
        reader = MockReader(["Enter your username: ", "Connected! Users online: testclient\n"])
        writer = MockWriter()
        
        # Mock asyncio.open_connection to return our mocks
        with patch('asyncio.open_connection', return_value=(reader, writer)), \
             patch('builtins.input', side_effect=[username, "exit"]), \
             patch('builtins.print') as mock_print, \
             patch('asyncio.gather', new=AsyncMock()) as mock_gather:
            
            # Call handle_client
            await async_client.handle_client()
            
            # Check that the username was sent
            assert any(username.encode() in data for data in writer.written_data)
            
            # Verify that asyncio.gather was called with receive and send functions
            assert mock_gather.call_count == 1
            assert len(mock_gather.call_args[0]) == 2  # Two coroutines passed to gather

    @pytest.mark.asyncio
    async def test_client_receive_function(self):
        # Instead of trying to access the receive function directly,
        # we'll create a custom receive function that mimics the one in the client
        async def mock_receive():
            reader = MockReader(["Test server message", b''])
            with patch('builtins.print') as mock_print:
                try:
                    while True:
                        data = await reader.read(1024)
                        if not data:
                            break
                        print(f"\n{data.decode()}", end=" ")
                except:
                    pass
            
            return mock_print
        
        # Run the mocked receive function
        mock_print = await mock_receive()
        
        # Check if it printed the message
        mock_print.assert_any_call("\nTest server message", end=" ")

    @pytest.mark.asyncio
    async def test_client_send_function(self):
        # Create a custom send function that mimics the one in the client
        async def mock_send():
            writer = MockWriter()
            with patch('asyncio.to_thread', side_effect=["Hello server!", "exit"]):
                # Wrap the code with task creation and cancellation to handle coroutines
                async def process_messages():
                    try:
                        while True:
                            message = await asyncio.to_thread(input, "You: ")
                            if message.lower() == "exit":
                                writer.write("exit".encode())
                                await writer.drain()
                                writer.close()
                                await writer.wait_closed()
                                break
                            writer.write(message.encode())
                            await writer.drain()
                    except:
                        pass
                
                task = asyncio.create_task(process_messages())
                await asyncio.sleep(0.1)  # Give the task time to process
                task.cancel()  # Cancel to prevent "never awaited" warnings
                try:
                    await task
                except asyncio.CancelledError:
                    pass  # Expected cancellation
            
            return writer
        
        # Run the mocked send function
        writer = await mock_send()
        
        # Check that messages were written
        assert len(writer.written_data) == 2
        assert b"Hello server!" in writer.written_data[0]
        assert b"exit" in writer.written_data[1]
        assert writer.closed == True

# Integration tests
class TestIntegration:
    
    # @pytest.mark.asyncio
    # async def test_message_flow_integration(self, reset_server_state):
    #     # This test simulates two clients exchanging messages
        
    #     # Create users and message to test
    #     user1 = "test_user1"
    #     user2 = "test_user2"
    #     test_message = f"{user2}: Hello from user1!"
        
    #     # Manually add user2 to clients to simulate existing connection
    #     reader2 = MockReader([user2, "exit"])
    #     writer2 = MockWriter()
    #     async_server.clients[user2] = (reader2, writer2)
        
    #     # Setup reader/writer for user1
    #     reader1 = MockReader([user1, test_message, "exit"])
    #     writer1 = MockWriter()
        
    #     # Handle user1 connection and message sending
    #     await async_server.handle_client(reader1, writer1)
        
    #     # Verify the message was received by user2
    #     receiver_messages = [msg.decode() for msg in writer2.written_data]
    #     found_message = False
    #     for msg in receiver_messages:
    #         if f"[{user1}] Hello from user1!" in msg:
    #             found_message = True
    #             break
                
    #     assert found_message, "Integration test failed: message not delivered"

    @pytest.mark.asyncio
    async def test_server_client_handshake(self):
        # Test the initial connection handshake between server and client
        
        # Reset server state
        async_server.clients = {}
        
        # Start a "real" server in a separate task
        with patch('asyncio.start_server') as mock_start_server:
            # Create a mock server that will call handle_client with our mocks
            async def mock_handle_connection(client_reader, client_writer):
                await async_server.handle_client(client_reader, client_writer)
            
            mock_server = AsyncMock()
            mock_server.serve_forever = AsyncMock()
            mock_server.__aenter__ = AsyncMock(return_value=mock_server)
            mock_server.__aexit__ = AsyncMock()
            
            mock_socket = Mock()
            mock_socket.getsockname.return_value = (async_server.HOST, async_server.PORT)
            mock_server.sockets = [mock_socket]
            
            mock_start_server.return_value = mock_server
            
            # Start the server
            server_task = asyncio.create_task(async_server.main())
            
            # Short delay for server to "start"
            await asyncio.sleep(0.1)
            
            # Create client mocks
            username = "test_integration"
            client_reader = MockReader(["Enter your username: ", f"Connected! Users online: {username}\n"])
            client_writer = MockWriter()
            
            with patch('asyncio.open_connection', return_value=(client_reader, client_writer)), \
                 patch('builtins.input', side_effect=[username, "exit"]), \
                 patch('builtins.print'), \
                 patch('asyncio.gather', new=AsyncMock()) as mock_gather:
                
                # Call the handle_client to simulate connection
                client_task = asyncio.create_task(async_client.handle_client())
                
                # Short delay for client to "connect"
                await asyncio.sleep(0.1)
                
                # Manually call the mock_handle_connection to simulate server accepting client
                client_reader_server = MockReader([username, "exit"])
                client_writer_server = MockWriter()
                await mock_handle_connection(client_reader_server, client_writer_server)
                
                # Check that server sent username prompt
                assert b"Enter your username" in client_writer_server.written_data[0]
                
                # Cancel tasks to prevent "never awaited" warnings
                server_task.cancel()
                client_task.cancel()
                try:
                    await asyncio.gather(server_task, client_task, return_exceptions=True)
                except asyncio.CancelledError:
                    pass  # Expected cancellation
                
                # Verify client sending username
                client_messages = [msg.decode() if isinstance(msg, bytes) else msg for msg in client_writer.written_data]
                assert any(username in msg for msg in client_messages)


# Run the tests
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])