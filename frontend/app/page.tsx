// @/app/page.tsx
'use client'

import {useEffect, useState} from 'react';
import io from 'socket.io-client';
import MapComponent from '@/app/components/Map';
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs"
import TravelLog from './components/TravelLog';
import TravelTrace from './components/TravelTrace';
import {getNewUserId} from './utils/api';
import Mails from './components/Mails';

const initialPosition = [120.00799, 30.293316];
const targetHost = 'http://47.236.129.49:8011';

export default function Home() {
  const [userId, setUserId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState("TravelLog");
  const [pinInfos, setPinInfos] = useState([]);

  useEffect(() => {
    const storedUserId = localStorage.getItem('userId');
    if (storedUserId) {
      setUserId(parseInt(storedUserId, 10));
    } else {
      getNewUserId().then(newId => {
        localStorage.setItem('userId', newId.toString());
        setUserId(newId);
      });
    }
  }, []);



  const handleTabChange = (value: string) => {
    setActiveTab(value);
  };

  const handlePinInfoUpdate = (newPinInfo) => {
    setPinInfos(prevInfos => [...prevInfos, newPinInfo]);
  };

  const mapWidth = activeTab === "TravelLog" ? "w-2/5" : "w-3/5";
  const contentWidth = activeTab === "TravelLog" ? "w-3/5" : "w-2/5";

  return (
    <div className="h-screen flex overflow-hidden">
      <div className={`${mapWidth} h-full`}>
        <MapComponent
          userId={userId}
          initialPosition={initialPosition}
          onPinInfoUpdate={handlePinInfoUpdate}
        />
      </div>
      <div className={`${contentWidth} h-full overflow-y-hidden p-6`}>
        <Tabs defaultValue="TravelLog" className="h-full flex flex-col" onValueChange={handleTabChange}>
          <TabsList>
            <TabsTrigger value="TravelLog">Travel Log</TabsTrigger>
            <TabsTrigger value="TravelTrace">Travel Trace</TabsTrigger>
            <TabsTrigger value="Mails">Mails</TabsTrigger>
          </TabsList>
          <TabsContent value="TravelLog" className="flex-grow overflow-hidden">
            {userId && <TravelLog userId={userId} />}
          </TabsContent>
          <TabsContent value="TravelTrace" className="flex-grow overflow-hidden">
            <TravelTrace pinInfos={pinInfos} />
          </TabsContent>
          <TabsContent value="Mails" className="flex-grow overflow-hidden">
            <Mails />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
