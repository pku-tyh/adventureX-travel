import React from 'react'
import { useChat } from 'ai/react'
import { cn } from "@/lib/utils"

const mockMessages = [
  {
    role: 'assistant',
    send_time: 1625097600000,
    message: 'Hello! How can I assist you today?',
    location: { x: 100, y: 200 },
    read: true,
    image_url: null,
    event: null
  },
  {
    role: 'user',
    send_time: 1625097660000,
    message: 'Hi there! I have a question about the game.',
    location: { x: 150, y: 250 },
    read: true,
    image_url: null,
    event: null
  },
  {
    role: 'assistant',
    send_time: 1625097720000,
    message: 'Of course! I\'d be happy to help. What would you like to know about the game?',
    location: { x: 100, y: 300 },
    read: false,
    image_url: null,
    event: null
  }
]

const Mails = () => {
  const { messages, input, handleSubmit, handleInputChange, isLoading } = useChat()

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {mockMessages.map((message, index) => (
          <div 
            key={index} 
            className={cn(
              "mb-4 p-3 rounded-lg max-w-[70%]",
              message.role === 'user' ? "bg-blue-100 ml-auto" : "bg-gray-100 mr-auto"
            )}
          >
            <div className="font-bold">{message.role}</div>
            <div>{message.message}</div>
            <div className="text-xs text-gray-500">
              {new Date(message.send_time).toLocaleString()}
            </div>
            {message.role === 'assistant' && (
              <button className="mt-2 px-2 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">
                Visit
              </button>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex">
          <input
            className="flex-grow p-2 border rounded-l"
            value={input}
            onChange={handleInputChange}
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <button 
            type="submit" 
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-r hover:bg-blue-600"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  )
}

export default Mails