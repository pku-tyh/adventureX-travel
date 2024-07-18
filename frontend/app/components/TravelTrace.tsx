// @/app/components/TravelTrace.jsx
import React, { useState, useEffect } from 'react'
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import Time from './Time'
import { Button } from '@/components/ui/button'

const TravelTrace = ({ pinInfos }) => {
  const [showTime, setShowTime] = useState(false)
  const [travelData, setTravelData] = useState([])

  useEffect(() => {
    if (pinInfos) {
      const newTravelData = pinInfos.map(info => ({
        city: info.city || "Unknown City",
        info: info.description || "No description available",
        imageUrl: info.image_url || "https://example.com/placeholder.jpg",
        date: info.date || new Date().toISOString().split('T')[0]
      }));
      setTravelData(newTravelData);
    }
  }, [pinInfos]);
  
  return (
    <div className="relative h-full">
      {showTime && (
        <div className="top-0 left-0 right-0 z-10 bg-white">
          <Time />
        </div>
      )}
      <ScrollArea className="w-full h-full" style={{ paddingTop: showTime ? '40px' : '0' }}>
        <div className="relative pl-8 m-6">
          {/* Timeline */}
          <div className="absolute left-4 top-0 bottom-0 w-px bg-gray-200"></div>

          {/* Travel cards */}
          {travelData.map((travel, index) => (
            <div key={index} className="mb-8">
              {/* Date and dot */}
              <div className="flex items-center mb-2">
                <div className="absolute left-[14px] w-4 h-4 bg-blue-500 rounded-full transform -translate-x-1/2"></div>
                <span className="text-sm text-gray-500">{travel.date}</span>
              </div>

              {/* Card */}
              <Card className="flex overflow-hidden">
                <img src={travel.imageUrl} alt={travel.city} className="w-1/3 h-40 object-cover" />
                <div className="p-4">
                  <h3 className="text-xl font-bold mb-2">{travel.city}</h3>
                  <p className="text-gray-600">{travel.info}</p>
                </div>
              </Card>
            </div>
          ))}
        </div>
      </ScrollArea>
      {!showTime && (
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-white">
          <div className='flex flex-col gap-2'>
          <Button onClick={() => setShowTime(true)}>开始旅行</Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default TravelTrace