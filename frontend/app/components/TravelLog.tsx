// @/app/components/TravelLog.tsx
import React, {useEffect, useState} from 'react'
import {getPinInfo} from '@/app/utils/api';
import {ScrollArea} from "@/components/ui/scroll-area"

interface TravelLogProps {
  userId: number;
}

interface PinInfo {
  name: string;
  location: { lat: number; lng: number };
  data: { image_url: string; info: string }[];
}

const TravelLog: React.FC<TravelLogProps> = ({ userId }) => {
  const [travelLog, setTravelLog] = useState<PinInfo | null>(null);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number }>({ lat: 30.293316, lng: 120.00799 });

  useEffect(() => {
    getPinInfo(userId, currentLocation).then(setTravelLog);
  }, [userId]);

  if (!travelLog) return <div>Loading...</div>;

  return (
    <ScrollArea className="w-full h-full bg-amber-50 p-6 rounded-lg">
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-center">旅行日志 - {travelLog.name}</h1>
        <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-3 gap-6">
          {travelLog.data.map((item, index) => (
            <div
              key={index}
              className="bg-white rounded-lg shadow-sm overflow-hidden transition-shadow duration-300 hover:shadow-md mb-6 break-inside-avoid"
            >
              <div className="aspect-w-16 aspect-h-9">
                <img src={item.image_url} alt="Travel" className="w-full h-full object-cover" />
              </div>
              <div className="p-4">
                <p className="text-gray-700 text-sm">{item.info}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </ScrollArea>
  )
}

export default TravelLog
