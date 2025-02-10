import React, { useState, useRef, useEffect, useMemo } from "react";
import ReactMarkdown from 'react-markdown';
import {
  SendIcon,
  BotIcon,
  CopyIcon,
  CircleX,
  RotateCw,
} from "lucide-react";
import { api } from "../lib/api";
import { Message } from "../lib/types";

import PdfViewer from "./PdfViewer";
import Loading from "./Loading";

const Modal = ({ children }) => {
  // simple Modal implementation based on Tailwind CSS classes
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 h-screen">
      <div className="bg-white p-4 rounded-lg shadow-lg max-w-3xl w-full mx-y relative h-full">
        {children}
      </div>
    </div>
  );
}

interface CurrentFileMeta {
  fileName: string;
  initialPageNumber: number;
  textToHighlight: string;
}

const ChatUI = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");

  // probably bad name choice. isLoading is used to show a loading spinner when bot is typing
  // loadingFile is used to show a loading spinner when a file is being loaded
  const [isLoading, setIsLoading] = useState(false);
  const [loadingFile, setLoadingFile] = useState(false);

  const [pdfContent, setPdfContent] = useState(null);
  const [currentFileMeta, setCurrentFileMeta] = useState<CurrentFileMeta | null>(null);

  // react-pdf requires the pdf content to be memoized to prevent re-rendering
  const memoizedPdfPointer = useMemo(() => ({ data: pdfContent }), [pdfContent]);



  // Reference to the bottom of the chat, mainly used for auto-scrolling
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Function to add messages with delay and simulate movement
  const initializeMessages = async () => {
    // send the first welcome message from the bot

    setMessages([
      { sender: "bot", content: "Hello 👋  \n How can I assist you today?" },
    ])

  };

  // Call the initialization function when component mounts
  useEffect(() => {
    initializeMessages();
  }, []);

  useEffect(() => {
    // scroll to the bottom of the chat
    // this effect is triggered whenever there is a new message
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (message: string) => {
    if (message.trim() !== "") {
      setMessages([...messages, { content: message, sender: "user" }]);
      setIsLoading(true);
      setInputMessage("");

      try {
        const data = await api.chat.send(message);

        setMessages(prevMessages => [...prevMessages, { content: data.content, sender: "bot", metadata: data.metadata }]);
        setIsLoading(false);
      } catch (error) {

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

  const handleCopyMessage = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // Optionally, you can show a brief notification that the text was copied
    }, (err) => {
      console.error('Could not copy text: ', err);
    });
  };

  const loadFile = async (fileName: string, query: string) => {
    setLoadingFile(true);
    try {
      const content = await api.getFile(fileName);
      const initialPageIndex = await api.getRelevantPageIndex(fileName, query);
      setCurrentFileMeta({
        fileName,
        initialPageNumber: initialPageIndex,
        textToHighlight: query,
      });
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
  };

  const renderMessage = (message: Message, index) => {
    return (
      <div
        key={index}
        // this defines the alignment of the message based on the sender
        // user messages are aligned to the right
        // bot messages are aligned to the left
        className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"
          } animate-fadeIn`}
      >
        <div
          className={`p-4 rounded-2xl max-w-screen-md ${message.sender === "user"
            ? "bg-slate-200 text-slate-800 w-1/4"
            : "bg-gray-100 text-gray-800 w-4/5"
            } shadow-xl flex`}
        >
          {message.sender === "bot" && (
            <BotIcon className="w-5 h-5 mr-3 mt-1 text-purple-400" />
          )}
          <div className="w-full">

            <ReactMarkdown components={{
              // improves the styping of paragraphs by adding Tailwind CSS class
              p: ({ node, ...props }) => <p className="text-balance" {...props} />
            }}>
              {message.content}
            </ReactMarkdown>
            
            {message.metadata && (
              message.metadata.map((meta, i) => (
                // for each file we show a button to download the file
                // if the file occures several times in the message, it will be shown multiple times
                // each time with a different query
                // click on the button will trigger the loadFile function
                // file will be loaded exactly on the page where the query is found
                <button
                  key={i}
                  onClick={() => loadFile(meta.file_name, meta.content)}
                  className="bg-white p-2 rounded-lg shadow-md mt-2 text-left max-w-3/4 w-full hover:bg-gray-100 transition-colors duration-200"
                >
                  <div className="flex justify-between items-center">
                    <div className="text-sm font-semibold text-gray-700">{meta.file_name}</div>
                    {meta.year && <div className="text-xs text-gray-900">{meta.year}</div>}
                  </div>
                  {meta.content && (
                    <div className="text-xs text-gray-500 mt-1 truncate max-w-72">{meta.content}</div>
                  )}
                </button>
              ))
            )}
            {message.sender === "bot" && message.has_error && (
              <div className="flex justify-center mt-2">
                <button onClick={() => {
                  // Remove the error message from the chat
                  // Retry the last message from user
                  const lastMessage = messages.filter((msg) => msg.sender === "user").pop();
                  handleSendMessage(lastMessage.content);
                }} className="flex items-center p-2 rounded-full bg-blue-600 hover:bg-blue-700 text-white">
                  <RotateCw className="w-4 h-4 mr-1" />
                  Retry
                </button>
              </div>
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
              </div>
            )}
          </div>
        </div>
      </div >
    );
  };

  return (
    <div className="flex h-screen font-sans">
      {/* Sidebar */}
      <div className="w-80 backdrop-filter backdrop-blur-lg p-6 flex flex-col border-r border-gray-100">

        <button className="flex items-center mb-8 justify-center" onClick={() => window.location.reload()}>
          <BotIcon className="w-7 h-7 text-purple-400 mr-1" />
          <span className="text-2xl font-bold text-gray-800">Chatten</span>
        </button>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-grow flex-col backdrop-filter backdrop-blur-md bg-stone-50">
        {/* Messages */}
        <div className="flex-grow overflow-y-auto p-8 space-y-6 custom-scrollbar">
          {messages.map((message, index) => renderMessage(message, index))}
          {isLoading && <Loading message="Preparing response..." />}
          <div ref={chatBottomRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 mx-auto w-full max-w-4xl">
          <div className="flex items-center bg-opacity-50 rounded-full shadow-2xl backdrop-filter backdrop-blur-sm">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage(inputMessage)}
              className="flex-grow px-6 py-4 bg-transparent outline-none placeholder-gray-400"
              placeholder="Type a message..."
              disabled={isLoading}
            />
            <button
              onClick={() => handleSendMessage(inputMessage)}
              className="p-3 rounded-full text-gray-400 hover:text-purple-400 transition-colors duration-200 mr-2"
            >
              <SendIcon className="w-5 h-5 transform rotate-45" />
            </button>
          </div>
          {loadingFile && (
            <Modal>
              <div className="flex flex-col items-center justify-center h-full">
                <Loading message="Loading file..." />
              </div>
            </Modal>
          )}
          {pdfContent && (
            <Modal>
              <div className="flex justify-between items-center mb-4">
                <div className="text-lg font-semibold text-gray-800">
                  📄 Preview {currentFileMeta.fileName.replace(".pdf", "")}
                </div>
                <button
                  onClick={() => setPdfContent(null)}
                  className="text-red-500 hover:text-red-700"
                >
                  <CircleX className="w-6 h-6" />
                </button>
              </div>
              <PdfViewer memoizedPdfPointer={memoizedPdfPointer} initialPageNumber={currentFileMeta.initialPageNumber} textToHighlight={currentFileMeta.textToHighlight} />
            </Modal>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatUI;
