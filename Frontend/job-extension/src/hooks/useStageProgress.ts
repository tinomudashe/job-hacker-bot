import { useState, useEffect, useCallback } from 'react';
import { Stage } from '../components/StageProgressIndicator';

interface ProgressUpdate {
  type: 'progress' | 'stage' | 'tool' | 'complete' | 'error';
  message?: string;
  stage?: string;
  tool?: string;
  data?: any;
}

const defaultStages: Stage[] = [
  { id: 'initialization', name: 'Initializing', status: 'pending' },
  { id: 'conversation', name: 'Processing Request', status: 'pending' },
  { id: 'tool_execution', name: 'Executing Tools', status: 'pending' },
  { id: 'data_persistence', name: 'Saving Data', status: 'pending' },
  { id: 'response_formatting', name: 'Formatting Response', status: 'pending' },
];

export const useStageProgress = (websocketUrl?: string) => {
  const [stages, setStages] = useState<Stage[]>(defaultStages);
  const [currentStage, setCurrentStage] = useState<string | undefined>();
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const [ws, setWs] = useState<WebSocket | null>(null);

  const reset = useCallback(() => {
    setStages(defaultStages);
    setCurrentStage(undefined);
    setIsComplete(false);
    setError(undefined);
  }, []);

  const updateStage = useCallback((stageName: string) => {
    setCurrentStage(stageName);
    setStages(prev => {
      const stageIndex = prev.findIndex(s => s.id === stageName);
      if (stageIndex === -1) return prev;
      
      return prev.map((stage, index) => {
        if (index < stageIndex) {
          return { ...stage, status: 'completed' as const };
        } else if (index === stageIndex) {
          return { ...stage, status: 'active' as const };
        } else {
          return { ...stage, status: 'pending' as const };
        }
      });
    });
  }, []);

  const completeAllStages = useCallback(() => {
    setStages(prev => prev.map(stage => ({ ...stage, status: 'completed' as const })));
    setCurrentStage(undefined);
    setIsComplete(true);
  }, []);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data: ProgressUpdate = JSON.parse(event.data);
      
      switch (data.type) {
        case 'stage':
          if (data.stage) {
            updateStage(data.stage);
          }
          break;
        
        case 'tool':
          // Tool execution is part of the tool_execution stage
          updateStage('tool_execution');
          break;
        
        case 'complete':
          completeAllStages();
          break;
        
        case 'error':
          setError(data.message || 'An error occurred');
          break;
        
        case 'progress':
          // Handle generic progress messages if needed
          if (data.message) {
            // Parse message for stage hints
            const message = data.message.toLowerCase();
            if (message.includes('initializ')) {
              updateStage('initialization');
            } else if (message.includes('process') || message.includes('understand')) {
              updateStage('conversation');
            } else if (message.includes('tool') || message.includes('execut')) {
              updateStage('tool_execution');
            } else if (message.includes('sav') || message.includes('stor')) {
              updateStage('data_persistence');
            } else if (message.includes('format') || message.includes('prepar')) {
              updateStage('response_formatting');
            }
          }
          break;
      }
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
    }
  }, [updateStage, completeAllStages]);

  useEffect(() => {
    if (!websocketUrl) return;

    const websocket = new WebSocket(websocketUrl);
    
    websocket.onopen = () => {
      console.log('WebSocket connected for stage progress');
    };
    
    websocket.onmessage = handleMessage;
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error');
    };
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    setWs(websocket);

    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, [websocketUrl, handleMessage]);

  // Manual stage update for testing or fallback
  const manualUpdateStage = useCallback((stageName: string) => {
    updateStage(stageName);
  }, [updateStage]);

  return {
    stages,
    currentStage,
    isComplete,
    error,
    reset,
    updateStage: manualUpdateStage,
    completeAllStages,
  };
};