import { useState, useEffect } from 'react';
import io from 'socket.io-client';

export const useLiveData = (dataTypes = ['inventory', 'sales']) => {
  const [liveData, setLiveData] = useState({});
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to your Flask-SocketIO backend
    const socket = io('http://localhost:5000', {
      transports: ['websocket']
    });

    socket.on('connect', () => {
      setIsConnected(true);
      
      // Subscribe to data channels
      dataTypes.forEach(type => {
        socket.emit('subscribe', type);
      });
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    // Handle incoming data updates
    socket.on('data-update', (update) => {
      setLiveData(prev => ({
        ...prev,
        [update.type]: update.data
      }));
    });

    // Initial data fetch
    const fetchInitialData = async () => {
      const responses = await Promise.all(
        dataTypes.map(type => 
          fetch(`http://localhost:5000/api/${type}`)
            .then(res => res.json())
        )
      );
      
      const initialData = {};
      dataTypes.forEach((type, i) => {
        initialData[type] = responses[i];
      });
      
      setLiveData(initialData);
    };

    fetchInitialData();

    return () => {
      socket.disconnect();
    };
  }, [dataTypes]);

  return {
    liveData,
    isConnected,
    lastUpdated: new Date().toISOString()
  };
};