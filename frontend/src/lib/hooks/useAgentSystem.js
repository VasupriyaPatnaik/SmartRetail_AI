import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

export const useAgentSystem = () => {
  const [agents, setAgents] = useState({
    inventoryAgent: { status: 'idle', lastUpdated: null },
    forecastingAgent: { status: 'idle', lastUpdated: null },
    supplierAgent: { status: 'idle', lastUpdated: null }
  });

  const [collaborationLog, setCollaborationLog] = useState([]);

  const triggerAgentAction = useCallback(async (agentName, action, payload = {}) => {
    try {
      setAgents(prev => ({
        ...prev,
        [agentName]: { ...prev[agentName], status: 'processing' }
      }));

      // Simulate API call to your Flask backend
      const response = await axios.post(`http://localhost:5000/api/${agentName}/${action}`, payload);
      
      setAgents(prev => ({
        ...prev,
        [agentName]: { 
          status: 'success', 
          lastUpdated: new Date().toISOString() 
        }
      }));

      // Log inter-agent communication
      setCollaborationLog(prev => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          agent: agentName,
          action,
          message: `Successfully processed ${action}`
        }
      ]);

      return response.data;
    } catch (error) {
      setAgents(prev => ({
        ...prev,
        [agentName]: { 
          status: 'error', 
          lastUpdated: new Date().toISOString() 
        }
      }));

      setCollaborationLog(prev => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          agent: agentName,
          action,
          message: `Failed: ${error.message}`,
          isError: true
        }
      ]);

      throw error;
    }
  }, []);

  // Simulate agent collaboration
  const optimizeInventory = useCallback(async () => {
    const results = {};
    
    // 1. Get forecast from forecasting agent
    results.forecast = await triggerAgentAction(
      'forecastingAgent', 
      'predict-demand',
      { period: '7d' }
    );

    // 2. Check stock levels
    results.inventory = await triggerAgentAction(
      'inventoryAgent',
      'get-levels'
    );

    // 3. Coordinate with supplier
    if (results.inventory.needsRestock) {
      results.supplier = await triggerAgentAction(
        'supplierAgent',
        'place-order',
        { 
          productId: results.inventory.lowStockItem,
          quantity: results.forecast.suggestedOrder 
        }
      );
    }

    return results;
  }, [triggerAgentAction]);

  return {
    agents,
    collaborationLog,
    triggerAgentAction,
    optimizeInventory
  };
};