import React, { useState, useEffect } from 'react';
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

const Time = () => {
  const [day, setDay] = useState(1);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [departure, setDeparture] = useState("出发地");
  const [destination, setDestination] = useState("目的地");
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // 这里可以添加逻辑来更新天数和进度
    // 例如，每24小时增加一天，进度每天增加一定百分比
  }, [currentTime]);

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-2">现在是旅程的第 {day} 天</h2>
      <p className="text-gray-600 mb-4">{currentTime.toLocaleTimeString()}</p>
      
      <div className="mb-2 flex justify-between text-sm text-gray-500">
        <span>{departure}</span>
        <span>{destination}</span>
      </div>
      <Progress value={progress} className="w-full" />
    </div>
  );
};

export default Time;