import React, { useState, useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import { toast } from 'react-toastify';
import * as api from '../services/api'; // Assuming api.js has the chat endpoint

const Chatbot = () => {
  const [message, setMessage] = useState('');
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const { isAuthenticated } = useSelector((state) => state.auth);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim() || !isAuthenticated) return;

    const userMessage = { sender: 'user', text: message };
    setConversation((prev) => [...prev, userMessage]);
    setMessage('');
    setLoading(true);

    try {
      const history = conversation.map(turn => turn.text);
      const response = await api.chatbotQuery({ message: message, conversation_history: history });
      const aiMessage = { sender: 'ai', text: response.response };
      setConversation((prev) => [...prev, aiMessage]);
    } catch (err) {
      toast.error(`Chatbot error: ${err.message}`);
      setConversation((prev) => [...prev, { sender: 'ai', text: 'Sorry, I am having trouble responding.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-md p-4">
      <h3 className="text-xl font-bold mb-4">AI Assistant</h3>
      <div className="flex-1 overflow-y-auto border rounded-md p-3 mb-4 bg-gray-50">
        {conversation.length === 0 ? (
          <p className="text-gray-500 text-center">Start a conversation with the AI assistant...</p>
        ) : (
          conversation.map((msg, index) => (
            <div
              key={index}
              className={`mb-2 ${
                msg.sender === 'user' ? 'text-right' : 'text-left'
              }`}
            >
              <span
                className={`inline-block px-4 py-2 rounded-lg ${
                  msg.sender === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-300 text-gray-800'
                }`}
              >
                {msg.text}
              </span>
            </div>
          ))
        )}
        {loading && (
          <div className="text-center text-gray-500">AI is thinking...</div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSendMessage} className="flex">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="flex-1 border rounded-l-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Type your message..."
          disabled={loading || !isAuthenticated}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded-r-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading || !isAuthenticated}
        >
          Send
        </button>
      </form>
      {!isAuthenticated && (
        <p className="text-red-500 text-sm mt-2">Please log in to use the chatbot.</p>
      )}
    </div>
  );
};

export default Chatbot;