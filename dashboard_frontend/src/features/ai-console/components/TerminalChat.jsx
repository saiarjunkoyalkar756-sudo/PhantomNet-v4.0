import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import copilotService from '@/services/copilot.service';

const TerminalChat = () => {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'ai', text: "Greetings, Operator. I am PhantomNet's Cognitive Assistant. How may I assist your cyber operations today? (e.g., 'Show me active threats', 'Check agent status', 'Run playbook Alpha')" }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage = input.trim();
    const newMessage = { id: Date.now(), sender: 'user', text: userMessage };
    setMessages((prev) => [...prev, newMessage]);
    setInput('');

    try {
      const response = await copilotService.getExplanation(userMessage);
      const aiResponse = { id: Date.now() + 1, sender: 'ai', text: response.data.explanation };
      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      const errorMessage = { id: Date.now() + 1, sender: 'ai', text: "Error getting response from AI. Please try again." };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };


  const messageVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="flex flex-col h-full bg-background rounded-lg border border-border overflow-hidden">
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full p-4">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                layout
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={messageVariants}
                className={`flex items-start mb-4 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'ai' && <Bot className="w-6 h-6 mr-3 text-primary flex-shrink-0" />}
                <div
                  className={`max-w-[70%] p-3 rounded-lg ${
                    msg.sender === 'user'
                      ? 'bg-secondary/30 text-text-primary border border-secondary self-end'
                      : 'bg-panel-solid border border-border text-text-primary self-start'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                </div>
                {msg.sender === 'user' && <User className="w-6 h-6 ml-3 text-text-secondary flex-shrink-0" />}
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </ScrollArea>
      </div>

      <div className="border-t border-border p-4 bg-panel-solid flex items-center">
        <Textarea
          placeholder="Ask PhantomNet AI..."
          className="flex-1 mr-4 bg-background border border-border focus:ring-primary focus:border-primary text-text-primary resize-none custom-scrollbar"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          rows={1}
        />
        <Button onClick={handleSendMessage} className="bg-primary hover:bg-primary/90 text-primary-foreground">
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

export default TerminalChat;
