// src/p2p_chat/frontend/App.js
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [username, setUsername] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [recipientInput, setRecipientInput] = useState('');
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [storedMessages, setStoredMessages] = useState([]);
  const [wsClient, setWsClient] = useState(null);
  
  const messagesEndRef = useRef(null);

  // Connect to WebSocket server
  const connectToServer = () => {
    if (!username) return;
    
    // Create WebSocket connection
    const ws = new WebSocket(`ws://localhost:5001/ws/${username}`);
    
    ws.onopen = () => {
      console.log('Connected to server');
      setIsConnected(true);
      setWsClient(ws);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'users_update') {
        setOnlineUsers(data.users);
      } 
      else if (data.type === 'stored_messages') {
        setStoredMessages(data.messages);
      }
      else if (data.type === 'chat') {
        setMessages(prev => [...prev, {
          sender: data.sender,
          message: data.message,
          timestamp: data.timestamp
        }]);
      }
      else if (data.type === 'notification') {
        setMessages(prev => [...prev, {
          sender: 'System',
          message: `${data.message} ${data.metadata ? JSON.stringify(data.metadata) : ''}`,
          timestamp: data.timestamp
        }]);
      }
    };
    
    ws.onclose = () => {
      console.log('Disconnected from server');
      setIsConnected(false);
      setWsClient(null);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };
  
  // Handle sending messages
  const sendMessage = () => {
    if (!isConnected || !inputMessage || !recipientInput) return;
    
    const message = {
      sender: username,
      destination: recipientInput,
      message: inputMessage,
      type: 'chat'
    };
    
    wsClient.send(JSON.stringify(message));
    
    // Add message to local display
    setMessages(prev => [...prev, {
      sender: `You (to ${recipientInput})`,
      message: inputMessage,
      timestamp: new Date().toISOString()
    }]);
    
    // Clear input fields
    setInputMessage('');
  };
  
  // Check for stored messages
  const checkStoredMessages = () => {
    if (!isConnected) return;
    
    const command = {
      type: 'command',
      command: '!check'
    };
    
    wsClient.send(JSON.stringify(command));
  };
  
  // Handle disconnect
  const disconnect = () => {
    if (wsClient) {
      try {
        wsClient.close(1000, "User disconnected");
      } catch (err) {
        console.error('Error disconnecting:', err);
      }
    }
    
    // Clear all messages and state when disconnecting
    setIsConnected(false);
    setWsClient(null);
    setMessages([]);
    setStoredMessages([]);
    setOnlineUsers([]);
    setUsername('');  // Reset username field
    setInputMessage('');
    setRecipientInput('');

    localStorage.removeItem('p2p-chat-messages');
    localStorage.removeItem('p2p-chat-user');
    window.location.reload();
  };
  
  // Replace the existing websocket.onclose handler:
  ws.onclose = (event) => {
    console.log('Disconnected from server:', event);
    setIsConnected(false);
    setWsClient(null);
    
    // Don't clear messages on unexpected disconnection
    // This way we only clear messages on explicit disconnect by the user
    if (!event.wasClean) {
      setConnectionError('Connection closed unexpectedly. The server might be down.');
    }
  };
  
  // Auto-scroll to bottom of message list
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, storedMessages]);

  // Subscribe to thermometer
  const subscribeToThermometer = () => {
    if (!isConnected) return;
    
    const command = {
      sender: username,
      destination: 'thermometer1',
      message: 'subscribe',
      type: 'chat'
    };
    
    wsClient.send(JSON.stringify(command));
  };
  
  return (
    <div className="app">
      <header className="header">
        <h1>P2P Chat</h1>
      </header>
      
      <main className="main">
        {!isConnected ? (
          <div className="login-container">
            <h2>Connect to Chat</h2>
            <input
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <button onClick={connectToServer}>Connect</button>
          </div>
        ) : (
          <div className="chat-container">
            <div className="sidebar">
              <div className="online-users">
                <h3>Online Users</h3>
                <ul>
                  {onlineUsers.map((user, index) => (
                    <li key={index} onClick={() => setRecipientInput(user)}>
                      {user}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="actions">
                <button onClick={checkStoredMessages}>Check Messages</button>
                <button onClick={subscribeToThermometer}>Subscribe to Thermometer</button>
                <button onClick={disconnect}>Disconnect</button>
              </div>
            </div>
            
            <div className="message-area">
              <div className="message-list">
                {messages.map((msg, index) => (
                  <div key={index} className="message">
                    <div className="message-header">
                      <span className="sender">{msg.sender}</span>
                      <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="message-body">{msg.message}</div>
                  </div>
                ))}
                
                {storedMessages.length > 0 && (
                  <div className="stored-messages">
                    <h4>Stored Messages</h4>
                    {storedMessages.map((msg, index) => (
                      <div key={`stored-${index}`} className="message stored">
                        <div className="message-header">
                          <span className="sender">{msg.sender}</span>
                          <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <div className="message-body">{msg.message}</div>
                      </div>
                    ))}
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              
              <div className="message-input">
                <input
                  type="text"
                  placeholder="Recipient"
                  value={recipientInput}
                  onChange={(e) => setRecipientInput(e.target.value)}
                />
                <input
                  type="text"
                  placeholder="Type your message..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                />
                <button onClick={sendMessage}>Send</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}



export default App;