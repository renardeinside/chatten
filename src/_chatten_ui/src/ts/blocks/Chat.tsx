import React, { useState, useRef, useEffect, useMemo } from "react";
import ReactMarkdown from 'react-markdown';
import {
  SendIcon,
  BotIcon,
  ThumbsUpIcon,
  ThumbsDownIcon,
  CopyIcon,
  CircleX,
} from "lucide-react";
import { api } from "../lib/api";
import { Message } from "../lib/types";
import { Document, Page } from 'react-pdf';

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

import { pdfjs } from 'react-pdf';
import PdfViewer from "./PdfViewer";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const Modal = ({ children }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 h-screen">
      <div className="bg-white p-4 rounded-lg shadow-lg max-w-3xl w-full mx-4 my-6 relative h-full">
        {children}
      </div>
    </div>
  );
}

const ChatUI = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const messagesEndRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState({});
  const initialized = useRef(false);
  const [pdfContent, setPdfContent] = useState(null);

  const memoizedPdfPointer = useMemo(() => ({ data: pdfContent }), [pdfContent]);

  const [loadingFile, setLoadingFile] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSendMessage = async () => {
    if (inputMessage.trim() !== "") {
      setMessages([...messages, { content: inputMessage, sender: "user" }]);
      setInputMessage("");
      setIsLoading(true);

      try {
        const data = await api.chat.send(inputMessage);

        setMessages(prevMessages => [...prevMessages, { content: data.content, sender: "bot", metadata: data.metadata }]);
        setIsLoading(false);
      } catch (error) {
        console.error('Error:', error);
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            content: `Sorry, I'm having trouble with providing the response. Error details: ${error.message}`,
            has_error: true,
            sender: "bot",
          },
        ]);
        setIsLoading(false);
      }
    }
  };

  const handleFeedback = (messageIndex, isPositive) => {
    setFeedback(prev => ({
      ...prev,
      [messageIndex]: isPositive
    }));
    // Here you would typically send this feedback to your backend
    console.log(`Feedback for message ${messageIndex}: ${isPositive ? 'positive' : 'negative'}`);
  };

  const handleCopyMessage = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // Optionally, you can show a brief notification that the text was copied
      console.log('Text copied to clipboard');
    }, (err) => {
      console.error('Could not copy text: ', err);
    });
  };

  const renderMessage = (message: Message, index) => {
    return (
      <div
        key={index}
        className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"
          } animate-fadeIn`}
      >
        <div
          className={`max-w-2xl p-4 rounded-2xl ${message.sender === "user"
            ? "bg-slate-200 text-slate-800"
            : "bg-gray-100 text-gray-800"
            } shadow-xl flex`}
        >
          {message.sender === "bot" && (
            <BotIcon className="w-5 h-5 mr-3 mt-1 text-purple-400" />
          )}
          <div className="markdown-content">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {message.metadata && (
              message.metadata.map((meta, i) => (
                <button
                  key={i}
                  onClick={async () => {
                    console.log(`Opening file: ${meta.file_name}`);
                    setLoadingFile(true);
                    try {
                      const content = await api.getFile(meta.file_name);
                      setPdfContent(content);
                    } catch (error) {
                      // add message to the chat
                      setMessages((prevMessages) => [
                        ...prevMessages,
                        {
                          content: `Sorry, I'm having trouble with downloading the file. Error details: ${error.message}`,
                          has_error: true,
                          sender: "bot",
                        },
                      ]);
                    } finally {
                      setLoadingFile(false);
                    }
                  }}
                  className="bg-white p-2 rounded-lg shadow-md mt-2 text-left w-full hover:bg-gray-100 transition-colors duration-200"
                >
                  <div className="text-sm font-semibold text-gray-700">{meta.file_name}</div>
                  <div className="text-xs text-gray-500">{meta.year}</div>
                  <div className="text-xs text-gray-500">Page {meta.chunk_num}</div>
                </button>
              ))
            )}
            {message.sender === "bot" && message.has_error && (
              <button onClick={() => handleSendMessage()} className="p-1 rounded-full bg-yellow-500 hover:bg-yellow-600">
                Retry
              </button>
            )}

            {message.sender === "bot" && (
              <div className="mt-2 flex justify-end space-x-2">
                <button
                  onClick={() => handleCopyMessage(message.content)}
                  className="p-1 rounded-full bg-gray-100 hover:bg-gray-300"
                  title="Copy message"
                >
                  <CopyIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleFeedback(index, true)}
                  className={`p-1 rounded-full ${feedback[index] === true ? 'bg-green-500' : 'bg-gray-100 hover:bg-gray-300'}`}
                >
                  <ThumbsUpIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleFeedback(index, false)}
                  className={`p-1 rounded-full ${feedback[index] === false ? 'bg-red-500' : 'bg-gray-100 hover:bg-gray-300'}`}
                >
                  <ThumbsDownIcon className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Function to add messages with delay and simulate movement
  const initializeMessages = async () => {
    // send the first welcome message from the bot

    setMessages([
      { sender: "bot", content: "Hello 👋  \n How can I assist you today?" },
    ])

  };

  // Call the initialization function when component mounts
  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true;
      initializeMessages();
    }
  }, []);

  return (
    <div className="flex h-screen font-sans">
      {/* Sidebar */}
      <div className="w-1/5 backdrop-filter backdrop-blur-lg p-6 flex flex-col border-r border-gray-100">

        <button className="flex items-center mb-8 justify-center">
          <BotIcon className="w-7 h-7 text-purple-400 mr-1" />
          <span className="text-2xl font-bold text-gray-800">Chatten</span>
        </button>
      </div>

      {/* Main Chat Area */}
      <div className="w-4/5 flex flex-col backdrop-filter backdrop-blur-md bg-stone-50">
        {/* Messages */}
        <div className="flex-grow overflow-y-auto p-8 space-y-6 custom-scrollbar">
          {messages.map((message, index) => renderMessage(message, index))}
          {isLoading && (
            <div className="flex justify-center items-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-800"></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 mx-auto w-full max-w-4xl">
          <div className="flex items-center bg-opacity-50 rounded-full shadow-2xl backdrop-filter backdrop-blur-sm">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              className="flex-grow px-6 py-4 bg-transparent outline-none placeholder-gray-400"
              placeholder="Type a message..."
              autoSave="on"
            />
            <button
              onClick={handleSendMessage}
              className="p-3 rounded-full text-gray-400 hover:text-purple-400 transition-colors duration-200 mr-2"
            >
              <SendIcon className="w-5 h-5 transform rotate-45" />
            </button>
          </div>
          {loadingFile && (
            <Modal>
              <div className="flex flex-col items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-800 mb-4"></div>
                <p className="text-gray-800">Loading PDF...</p>
              </div>
            </Modal>
          )}
          {pdfContent && (
            <Modal>
              <div className="flex justify-between items-center mb-4">
                <div className="text-lg font-semibold text-gray-800">
                  Document Preview
                </div>
                <button
                  onClick={() => setPdfContent(null)}
                  className="text-red-500 hover:text-red-700"
                >
                  <CircleX className="w-6 h-6" />
                </button>
              </div>
              <PdfViewer memoizedPdfPointer={memoizedPdfPointer} />
            </Modal>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatUI;
